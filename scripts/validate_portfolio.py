#!/usr/bin/env python3
"""Developer-only expanded graph verification. Never imported by business APIs."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from mock_enterprise.config import Settings
from mock_enterprise.core import Identity,canonical
from mock_enterprise.db import MODELS,read_store
from mock_enterprise.seed import initialize,load_seed,validate_graph
from mock_enterprise.domains.validation_rules import context,coverage,calculate_option
from mock_enterprise.snapshots import plan_digest,check_live
ROOT=Path(__file__).resolve().parents[1]

def validate_portfolio():
    rows,meta=load_seed(); validate_graph(rows)
    again,again_meta=load_seed()
    assert canonical(rows)==canonical(again) and meta==again_meta
    (ROOT/'.cache/tmp').mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory(prefix='portfolio-validator-',dir=ROOT/'.cache/tmp') as directory:
        p=Path(directory);settings=Settings(p/'demo.sqlite3',p,True);initialize(settings)
        with read_store(settings.db_path) as store:
            counts={k:len(store.list(k)) for k in MODELS}
            actor=Identity('validator','reader');ctx=context(store,actor,'CR-017')
            assert not coverage(store,actor,ctx)['coverage_satisfied']
            options=[calculate_option(store,actor,ctx,slot,sample) for slot in store.list('validation.slot',actor) for sample in store.list('validation.sample',actor)]
            assert len(options)==9
            assert {(o['cost_cents'],o['timing']['deadline_slack_minutes']) for o in options if o['resource_eligible']}=={(0,-1680),(180000,1320)}
            assert ctx['change']['current_plan_id'] is None and ctx['target']['status']=='requested'
            for plan in store.list('engineering.plan'):
                scoped=Identity('validator','reader',plan['program_id'],plan['customer_id'])
                jobs=store.list('validation.job',scoped,plan_id=plan['id'])
                assert plan_digest(plan)==plan['plan_digest']
                check_live(store,scoped,plan,job=jobs[0] if jobs else None)
            counts['audit_events']=store.con.execute('SELECT COUNT(*) FROM audit_events').fetchone()[0]
            counts['dependencies']=sum(len(m['dependencies']) for m in store.list('planner.milestone'))
            assert not store.con.execute('PRAGMA foreign_key_check').fetchall()
    return {'generator_version':meta['generator_version'],'counts':counts,'deterministic':True,'golden_path_inputs_preserved':True,'status':'PASS — isolated source graph and approval snapshot validation; no AI or physical test executed'}

if __name__=='__main__':print(json.dumps(validate_portfolio(),indent=2))
