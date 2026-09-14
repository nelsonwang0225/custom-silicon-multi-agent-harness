"""Scoped HTTP portfolio reads, assembled only from persisted business records."""
import json
from fastapi import APIRouter, Request
from . import schemas as m
from .core import at, identity
from .db import read_store
from .domains.validation_rules import context, coverage
from .views import plan_view, job_view, link_view

router=APIRouter(tags=['Portfolio discovery'])

class CaseData(m.Model):
    change: m.ChangeView
    baseline: m.Requirement
    target: m.Requirement
    baselineWorkload: m.Workload
    targetWorkload: m.Workload
    config: m.Configuration
    coverage: m.Coverage
    options: list[m.Option]
    milestone: m.Milestone
    jobs: list[m.JobView]
    links: list[m.LinkView]
    audit: list[m.AuditEvent]
    procedures: list[m.Procedure]
    policies: list[m.Policy]
    criteria: m.Criteria

class Portfolio(m.Model):
    cases: list[CaseData]
    milestones: list[m.Milestone]
    rates: list[m.Rate]
    samples: list[m.Sample]
    slots: list[m.Slot]
    labs: list[m.Lab]
    documents: list[m.DocumentMetadata]
    history: list[m.HistoricalJob]
    activity: list[m.AuditEvent]

@router.get('/portfolio',response_model=Portfolio,operation_id='read_operating_portfolio')
def portfolio(request: Request):
    """Transaction-consistent read model. Expensive option calculations remain per-case."""
    with read_store(request.app.state.settings.db_path) as store:
        actor=identity(request)
        programs=store.list('planner.program',actor)
        allowed={p['id'] for p in programs}
        events=[{'sequence':r['sequence'],**json.loads(r['data'])} for r in store.con.execute('SELECT sequence,data FROM audit_events ORDER BY sequence') if r['data']]
        events=[e for e in events if e['program_id'] in allowed]
        cases=[];evidence={}
        for change in store.list('engineering.change',actor):
            scoped=actor.scoped(change['program_id'],change['customer_id'])
            ctx=context(store,scoped,change['id'])
            key=(ctx['config']['id'],ctx['workload']['id'],ctx['criteria']['id'],ctx['procedure']['id'])
            if key not in evidence:evidence[key]=coverage(store,scoped,ctx)
            plans=[plan_view(store,scoped,p) for p in store.list('engineering.plan',scoped,change_id=change['id'])]
            current=next((p for p in plans if p['id']==change['current_plan_id']),None)
            cases.append(dict(change={**change,'plans':plans,'execution_state':current['execution_state'] if current else 'not_scheduled'},baseline=ctx['baseline'],target=ctx['target'],baselineWorkload=store.get('engineering.workload',ctx['baseline']['workload_profile_id'],scoped),targetWorkload=ctx['workload'],config=ctx['config'],coverage={**evidence[key],'change_id':change['id']},options=[],milestone=ctx['milestone'],jobs=[job_view(store,scoped,j) for j in store.list('validation.job',scoped,change_id=change['id'])],links=[link_view(store,scoped,l) for l in store.list('planner.link',scoped,change_id=change['id'])],audit=[e for e in events if e['change_id']==change['id']],procedures=[ctx['procedure']],policies=[ctx['policy']],criteria=ctx['criteria']))
        return dict(cases=cases,milestones=store.list('planner.milestone',actor),rates=[r for r in store.list('erp.rate',actor) if r['status']=='approved' and at(r['effective_from']) <= at(store.now) < at(r['effective_to'])],samples=store.list('validation.sample',actor),slots=store.list('validation.slot',actor),labs=store.list('validation.lab',actor),documents=[{k:v for k,v in d.items() if k!='content'} for p in programs for d in store.list('engineering.document',actor,program_id=p['id'])],history=store.list('validation.history',actor) if store.con.execute("SELECT 1 FROM sqlite_master WHERE name='validation_history'").fetchone() else [],activity=events)

@router.get('/validation/history/{job_id}',response_model=m.HistoricalJob,operation_id='get_historical_validation_job')
def historical_job(job_id: str,request: Request):
    with read_store(request.app.state.settings.db_path) as store:
        return store.get('validation.history',job_id,identity(request))
