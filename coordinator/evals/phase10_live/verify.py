"""Explicit paid analysis probe; isolated source data, no human approvals."""
import argparse
import json
import logging
import time
from uuid import uuid4
from pathlib import Path
from fastapi.testclient import TestClient
from coordinator.evals.phase08_5.probe import environment
from program_investigator.config import PROJECT, MODEL
from program_coordinator.control_host.runtime import DemoInvestigation
from program_coordinator.control_host.demo_management import DemoManagement
from program_coordinator.control_host.server import create_app

HEADERS = {'Origin':'http://testserver', 'X-Stratos-Action':'1',
           'X-Stratos-Demo-Profile':'automation', 'X-Stratos-Demo-Maintainer':'local-demo-reset'}


def summarize(root):
    """Read saved observations without repeating paid calls or source writes."""
    from program_coordinator.application.store import ActivityStore
    root=root.resolve()
    if not root.is_relative_to(PROJECT/'.cache/phase10-live') or not (root/'metadata/workflow-index.json').is_file():
        raise ValueError('ISOLATED_LIVE_ARTIFACTS_REQUIRED')
    store=ActivityStore(root/'metadata')
    with store.transaction() as data:
        results={}
        for run in data.runs.values():
            case=data.cases[run.case_id].change_id
            path=root/'metadata/runs'/run.run_id/'report.json'
            report=json.loads(path.read_text()) if path.is_file() else {}
            calls_path=path.parent/'tool-calls.json'
            calls=json.loads(calls_path.read_text()) if calls_path.is_file() else []
            progress=data.quality_recoveries.get(run.run_id) or data.standard_handoffs.get(run.run_id) or data.delivery_commitments.get(run.run_id)
            results[case]={'run_id':run.run_id,'status':run.status,'execution_mode':run.execution_mode,
                'error_code':run.error_code,'policy_path':report.get('policy_path'),
                'api_requests':report.get('api_requests',[]),'usage':report.get('usage',{}),
                'generations':len(report.get('generations',[])), 'tool_calls':report.get('tool_calls_started',len(calls)),
                'elapsed_ms':report.get('latency_ms'),'termination_reason':report.get('termination_reason'),
                'handoff_or_review_status':progress.status if progress else None}
        result={'model':MODEL,'cases':results,
            'scope':'Saved live analyses and policy-authorized intakes. No human approvals, governed execution, lab results or acceptance performed.'}
        (root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'report':str(root/'verification.json'), **result}),flush=True)
        return 0 if all(results.get(c,{}).get('status')=='completed' and results[c]['generations']>0 for c in ('CR-017','CR-019','QE-004','DR-009')) and results.get('QE-011',{}).get('handoff_or_review_status')=='handoff_verified' else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--run-paid',action='store_true')
    mode.add_argument('--summarize',type=Path,help='Summarize existing isolated artifacts without calling any model or source API')
    args=parser.parse_args()
    if args.summarize:return summarize(args.summarize)
    root=PROJECT/'.cache/phase10-live'/('verify_'+uuid4().hex)
    # Provider/SDK log payloads are not a verification artifact. Retain only the
    # existing sanitized run artifacts and the safe observations below.
    logging.disable(logging.CRITICAL)
    with environment(root) as (host,settings,_):
        host.mode='live_model'
        host.investigate=DemoInvestigation(host.config,host.store)
        host.max_concurrent_workflow_runs=5
        host.demo_management=DemoManagement(host,settings)
        with TestClient(create_app(host,allowed_origins=('http://testserver',),allowed_hosts=('testserver',))) as client:
            def post(path,body):
                response=client.post('/control-api/'+path,headers=HEADERS,json=body)
                if response.status_code not in (200,202):
                    raise RuntimeError('PROBE_HOST_REQUEST_FAILED_'+str(response.status_code))
                return response.json()
            post('demo/reset',{'scope':'full','confirmation':'RESET','expected_epoch':host.demo_management.state().epoch})
            post('demo/autonomous/enter',{'expected_epoch':host.demo_management.state().epoch})
            ids={}
            for case in ('CR-017','CR-019','QE-004','DR-009'):
                response=post('cases/'+case+'/investigations',{'invocation_id':'ui_live_'+uuid4().hex,'change_id':case,
                    'workflow_id':{'QE-004':'yield_exception_recovery','DR-009':'delivery_readiness'}.get(case,'requirement_change_analysis')})
                ids[case]=response['run_id']
            print(json.dumps({'status':'started','root':str(root),'model':MODEL,'runs':ids}),flush=True)
            started=time.monotonic(); seen={}
            while time.monotonic()-started<1000:
                with host.store.transaction() as data:
                    runs={case:data.runs[rid] for case,rid in ids.items()}
                states={case:r.status for case,r in runs.items()}
                if states!=seen:
                    print(json.dumps({'elapsed_seconds':round(time.monotonic()-started),'states':states}),flush=True)
                    seen=states
                if not host.tasks and all(r.status!='running' for r in runs.values()) and host.autonomous.status().status not in {'armed','event_emitted','workflow_running'}:
                    break
                time.sleep(2)
            return summarize(root)

if __name__=='__main__':raise SystemExit(main())
