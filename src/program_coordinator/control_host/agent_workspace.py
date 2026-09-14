"""Bounded business-level projection of existing host/checkpoint observations.

No source probes, credential reads, model calls, mutation or monitoring store.
Checkpoint time is a host observation, not a model heartbeat or task duration.
"""
from datetime import datetime, timezone
from typing import Literal
from fastapi import Request
from pydantic import Field
from ..models import Model, CaseState, Role, SourceReference
from ..application.models import WorkflowError, now_utc
from ..application.observability import visible
from .access import SCOPE, CASES, require_surface, route_allowed
from .operations import health

AGENTS = {
    'coordinator': ('Program Coordinator', 'Coordinator'),
    'change_impact': ('Change Impact Specialist', 'Change impact'),
    'validation_evidence': ('Validation & Evidence Specialist', 'Validation'),
    'program_commercial': ('Program / Commercial Impact Specialist', 'Program & commercial'),
    'manufacturing': ('Manufacturing Specialist', 'Manufacturing'),
}
OBSERVATION_TTL = 90
READ_TTL = 30
State = Literal['working','delegated','queued','completed','failed','cancelled','not_invoked','idle','unknown']

class WorkspaceLink(Model):
    label: str
    href: str

class AgentTask(Model):
    invocation_id: str | None = None
    state: State
    label: str
    observed_at: str | None = None
    finding: str | None = None
    evidence: list[SourceReference] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    error: str | None = None

class WorkspaceAgent(Model):
    id: Role
    name: str
    short_name: str
    state: State
    label: str
    tasks: list[AgentTask] = Field(default_factory=list)
    # Only observed caller edges, never the static permissions graph.
    callers: list[Role] = Field(default_factory=list)

class WorkHandoff(Model):
    kind: Literal['human','external','host','attention','complete']
    label: str
    record_id: str | None = None
    version: int | None = None
    digest: str | None = None
    observed_at: str | None = None

class WorkspaceRun(Model):
    run_id: str
    case_id: str
    status: str
    workflow_id: str = ""
    invocation_source: str = "User initiated"
    started_at: str
    completed_at: str | None
    execution_mode: str
    demo_pacing_min_seconds: int = 0
    observed_at: str | None
    telemetry: Literal['current','recorded','stale','unavailable']
    agents: list[WorkspaceAgent] = Field(default_factory=list)
    handoff: WorkHandoff | None = None
    links: list[WorkspaceLink] = Field(default_factory=list)

class WorkspaceSnapshot(Model):
    customer_id: str = SCOPE[0]
    program_id: str = SCOPE[1]
    read_at: str
    read_ttl_seconds: int = READ_TTL
    observation_ttl_seconds: int = OBSERVATION_TTL
    host_state: str = 'Available'
    runtime_mode: str
    model_state: str
    last_completed_model_run_at: str | None = None
    sources: list[dict[str, str | None]]
    fresh_source_count: int | None
    total_permitted_runs: int
    active_run_count: int
    runs: list[WorkspaceRun]
    selected_run_id: str | None


def age(value, now):
    try: return (datetime.fromisoformat(now.replace('Z','+00:00')) - datetime.fromisoformat(value.replace('Z','+00:00'))).total_seconds()
    except (ValueError, TypeError, AttributeError): return None


def checkpoint(host, run, case):
    path = host.checkpoint_path(run)
    if not path.exists(): return None, None
    try:
        if path.is_symlink() or path.parent.is_symlink() or path.stat().st_size > 4_000_000:
            raise ValueError('unsafe checkpoint')
        value = CaseState.model_validate_json(path.read_text())
        if (value.run_id, value.case_id, value.customer_id, value.program_id, value.event.change_id) != (run.run_id, run.case_id, *SCOPE, case):
            raise ValueError('checkpoint scope mismatch')
        stamp = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat().replace('+00:00','Z')
        return value, stamp
    except (ValueError, OSError): return None, None


def handoff(data, run, events):
    observed = max((e.timestamp for e in events),default=run.completed_at)
    def work(kind, label, **kw):return WorkHandoff(kind=kind,label=label,observed_at=observed,**kw)
    if run.status in {'failed','cancelled'}:return work('attention','Investigation incomplete · Inspect findings')
    if run.status=='running':return None
    h=data.standard_handoffs.get(run.run_id)
    if h:
        if h.status=='handoff_verified':return work('external','Handoff verified · Lab authorization pending',record_id=h.intake.id if h.intake else None,version=h.version)
        if h.status=='review_required':return work('attention','Standard route requires escalation',version=h.version)
        return work('host','Validation Operations intake · '+h.status.replace('_',' '),version=h.version)
    p=data.quality_recoveries.get(run.run_id) or data.delivery_commitments.get(run.run_id)
    if p:
        exact=dict(record_id=p.plan_id,version=p.plan_version,digest=p.plan_digest)
        if p.status == 'handoff_verified':return work('complete','Quality investigation handoff verified')
        if p.status in {'verified','commitment_current'}:
            return work('external','Recovery metadata verified · Disposition pending' if run.run_id in data.quality_recoveries else 'Commitment verified · Customer agreement pending',**exact)
        if p.status=='awaiting_review' and p.decision is None:return work('human','Awaiting Program Owner review',**exact)
        if p.decision=='approve':return work('host','Approved · Host execution pending',**exact)
        return work('attention',p.status.replace('_',' ').capitalize(),**exact)
    executions=[e for e in data.executions.values() if e.reference.run_id==run.run_id]
    if executions:
        e=executions[-1]; ref=e.reference
        exact=dict(record_id=ref.proposal_id,version=ref.proposal_version,digest=ref.proposal_digest)
        if e.status in {'proposal_ready','waiting_for_approval'}:return work('human','Awaiting Engineering review',**exact)
        if e.status=='completed_execution':return work('external','Scheduling verified · Physical evidence remains separate',**exact)
        if e.status=='approved':return work('host','Approved · Host execution pending',**exact)
        return work('attention',e.status.replace('_',' ').capitalize(),**exact)
    if run.status=='completed':return work('complete','Analysis complete · Inspect current case')
    return None


def tasks_for(run, state, stamp, telemetry, role):
    if state is None:
        if role=='coordinator' and run.status in {'completed','failed','cancelled'}:
            return [AgentTask(state=run.status,label='Run complete' if run.status=='completed' else 'Run incomplete',observed_at=run.completed_at)]
        return []
    if role=='coordinator':
        status = run.status
        label = 'Investigating'
        if status=='running':
            if state.workflow_stage=='specialists':status,label='delegated','With specialists'
            else:
                status='working'
                label={'triage':'Scoping work','reconcile':'Reconciling findings','synthesis':'Preparing assessment'}.get(state.workflow_stage,'Investigating')
        else: label='Run complete' if status=='completed' else 'Run incomplete'
        if telemetry=='stale' and status in {'working','delegated'}:status,label='unknown','Observation stale'
        package=run.recommendation
        return [AgentTask(state=status,label=label,observed_at=stamp,
            finding=visible(package.change_summary) if package else None,
            evidence=package.source_references[:16] if package else [],
            dependencies=[visible(q) for q in (package.unresolved_questions if package else state.unresolved_questions)[:4]],
            error='Investigation failed' if run.status=='failed' else None)]
    assessments={a.invocation_id:a.assessment for a in state.completed_assessments}
    result=[]
    for i in state.requested_specialists:
        if i.specialist!=role:continue
        a=assessments.get(i.invocation_id)
        status={'running':'working','pending':'queued'}.get(i.status,i.status)
        # Typed task category, not model-authored question/rationale or invented tool progress.
        label={'working':'Investigating','queued':'Requested','completed':'Task complete','failed':'Task failed','cancelled':'Task cancelled'}[status]
        if i.result_kind=='validation_clarification' and status=='working':label='Clarifying evidence'
        if (telemetry=='stale' or run.status!='running') and status in {'working','queued'}:status,label='unknown','No current observation'
        result.append(AgentTask(invocation_id=i.invocation_id,state=status,label=label,observed_at=stamp,
            finding=visible(a.summary) if a else None,evidence=a.source_references[:16] if a else [],
            dependencies=[visible(q) for q in a.unresolved_questions[:4]] if a else [],error='Specialist invocation failed' if i.error else None))
    return result


def snapshot(host, actor, selected=None, *, now=None):
    require_surface(actor,'overview')
    now=now or now_utc()
    with host.store.transaction() as data:
        runs=[r for r in data.runs.values() if (r.customer_id,r.program_id)==SCOPE and
              (c:=data.cases.get(r.case_id)) and (c.customer_id,c.program_id)==SCOPE and c.change_id in CASES]
        latest={}
        for r in sorted(runs,key=lambda r:r.started_at):latest[r.case_id]=r.run_id
        def current_outcome(r):
            return latest[r.case_id]==r.run_id and (r.run_id in data.quality_recoveries or r.run_id in data.delivery_commitments
                or r.run_id in data.standard_handoffs or any(e.reference.run_id==r.run_id for e in data.executions.values()))
        runs.sort(key=lambda r:(r.status=='running',current_outcome(r) if r.status!='running' else False,r.started_at,r.run_id),reverse=True)
        if selected == 'all': selected = None # Legacy URLs still select one run.
        if selected is not None and not any(r.run_id==selected for r in runs):raise WorkflowError('RUN_NOT_FOUND')
        chosen=selected if selected is not None else (runs[0].run_id if runs else None)
        kept=[r for r in runs if r.status=='running' or r.run_id==chosen or r in runs[:24]]
        views=[]
        for r in kept:
            case=data.cases[r.case_id].change_id
            events=[e for e in data.activity if e.run_id==r.run_id and (e.customer_id,e.program_id)==SCOPE and e.case_id==r.case_id]
            state,stamp=checkpoint(host,r,case)
            elapsed=age(stamp or r.started_at,now)
            telemetry='unavailable' if state is None else 'stale' if r.status=='running' and (elapsed is None or elapsed < -5 or elapsed>OBSERVATION_TTL) else 'current' if r.status=='running' else 'recorded'
            agents=[]
            for role,(name,short) in AGENTS.items():
                tasks=tasks_for(r,state,stamp,telemetry,role)
                status=next((s for s in ('failed','working','queued','unknown','delegated','cancelled','completed') if any(t.state==s for t in tasks)), 'unknown' if state is None else 'not_invoked')
                label=next((t.label for t in reversed(tasks) if t.state==status),'Telemetry unavailable' if state is None else 'Not invoked')
                callers=list(dict.fromkeys(i.caller for i in state.requested_specialists if i.specialist==role and i.status!='pending')) if state else []
                agents.append(WorkspaceAgent(id=role,name=name,short_name=short,state=status,label=label,tasks=tasks,callers=callers))
            path=f'/control/programs/PRG-A17/cases/{case}'
            links=[WorkspaceLink(label='Open case',href=path)]
            run_path='/control/runs/'+r.run_id
            if route_allowed(actor,run_path):links.append(WorkspaceLink(label='View run',href=run_path))
            views.append(WorkspaceRun(run_id=r.run_id,case_id=case,status=r.status,started_at=r.started_at,completed_at=r.completed_at,
                workflow_id=r.workflow_id,invocation_source='Source event' if r.trigger.kind=='source_event' else 'Concierge' if r.invocation_id.startswith('ui_chat_') else 'User initiated',
                execution_mode=r.execution_mode,
                demo_pacing_min_seconds=state.demo_pacing_min_seconds if state and case=='QE-011' and r.execution_mode=='deterministic_test' else 0,
                observed_at=stamp,telemetry=telemetry,agents=agents,handoff=handoff(data,r,events),links=links))
    sources=health(host) # Existing cached explicit checks only; no probes on render.
    fresh=[s for s in sources if s.checked_at and (a:=age(s.checked_at,now)) is not None and 0<=a<=300 and s.status=='Available']
    checked=any(s.checked_at for s in sources)
    return WorkspaceSnapshot(read_at=now,runtime_mode=host.mode,
        model_state='Deterministic test runtime' if host.mode=='deterministic_test' else 'Not checked',
        last_completed_model_run_at=max((r.completed_at for r in runs if r.execution_mode=='live_model' and r.status=='completed' and r.completed_at),default=None),
        sources=[dict(system=s.system,status=s.status,checked_at=s.checked_at) for s in sources],fresh_source_count=len(fresh) if checked else None,
        total_permitted_runs=len(runs),active_run_count=sum(r.status=='running' for r in runs),runs=views,selected_run_id=None if chosen=='all' else chosen)


def attach(app,host,actor):
    @app.get('/control-api/agent-workspace',response_model=WorkspaceSnapshot)
    def read(request:Request,run_id:str|None=None,customer_id:str=SCOPE[0],program_id:str=SCOPE[1]):
        selected=actor(request)
        if (customer_id,program_id)!=SCOPE:raise WorkflowError('SCOPE_FORBIDDEN')
        return snapshot(host,selected,run_id)
