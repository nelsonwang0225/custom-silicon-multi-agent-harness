"""Host-owned demo presentation and action projection, never client authority.

Surface access is distinct from source-scoped business reads and exact source
approval. Existing services still validate current plans, actors and manifests.
These public selectors provide no authentication of a real person.
"""
from urllib.parse import urlsplit
from typing import Literal
from ..models import Model
from ..application.demo_identity import READER, AUTOMATION, ENGINEER, PROGRAM_OWNER
from ..application.models import WorkflowError

ACTORS = {'reader': READER, 'automation': AUTOMATION, 'engineer': ENGINEER, 'program_owner': PROGRAM_OWNER}
SCOPE = ('CUST-FML01', 'PRG-A17')
CASES = ('CR-017', 'CR-019', 'QE-004', 'DR-009', 'QE-011')
Surface = Literal['overview', 'programs', 'workflows', 'decisions', 'scenarios', 'knowledge', 'operations']
Action = Literal['investigate', 'prepare', 'escalate', 'review', 'execute', 'reconcile', 'reassess', 'review_evidence']

# The existing host endpoint/service identity rules, separated from readiness.
ACTION_ACTORS = {
    'CR-017': {'investigate': (AUTOMATION, ENGINEER, PROGRAM_OWNER), 'prepare': (AUTOMATION, ENGINEER),
               'escalate': (AUTOMATION,),
               'review': (ENGINEER,), 'execute': (AUTOMATION, ENGINEER),
               'reconcile': (AUTOMATION, ENGINEER), 'reassess': (AUTOMATION, ENGINEER), 'review_evidence': (ENGINEER,)},
    'CR-019': {'investigate': (AUTOMATION, ENGINEER), 'reconcile': (AUTOMATION, ENGINEER)},
    'QE-004': {'investigate': (AUTOMATION, ENGINEER, PROGRAM_OWNER), 'escalate': (AUTOMATION,), 'review': (PROGRAM_OWNER,),
               'execute': (AUTOMATION, PROGRAM_OWNER), 'reconcile': (AUTOMATION,)},
    'DR-009': {'investigate': (AUTOMATION, ENGINEER, PROGRAM_OWNER), 'review': (PROGRAM_OWNER,),
               'execute': (AUTOMATION, PROGRAM_OWNER), 'reconcile': (AUTOMATION,)},
}
ACTION_ACTORS['QE-011'] = ACTION_ACTORS['QE-004']
SURFACES = {
    'automation': ('overview','programs','workflows','decisions','scenarios','knowledge','operations'),
    'engineer': ('overview','programs','decisions','scenarios','knowledge'),
    'program_owner': ('overview','programs','decisions','scenarios'),
    'reader': ('overview','programs','knowledge'),
}
DECISIONS = {'automation': ('validation_authorization','engineering_evidence','quality_recovery','delivery_commitment'),
             'engineer': ('validation_authorization','engineering_evidence','engineering_escalation'),
             'program_owner': ('quality_recovery','delivery_commitment'), 'reader': ()}
# Explicit installed story IDs/families; never classify using display titles.
SCENARIOS = {'automation': ('CR-017','CR-019','QE-004','DR-009'), 'engineer': ('CR-017','CR-019'),
             'program_owner': ('QE-004','DR-009'), 'reader': ()}

class Capabilities(Model):
    actor_id: str
    role: str
    selected: bool
    customer_id: str = SCOPE[0]
    program_id: str = SCOPE[1]
    surfaces: list[Surface]
    case_actions: dict[str, list[Action]]
    action_roles: dict[str, dict[str, list[str]]]
    decision_kinds: list[str]
    scenario_ids: list[str]
    automation_save: bool
    concierge_qa: bool = True
    demo_controls: bool

def resolve_actor(request, write=False):
    selector = request.headers.get('x-stratos-demo-profile')
    if selector is None:
        if write: raise WorkflowError('DEMO_IDENTITY_REQUIRED')
        return READER
    if selector not in ACTORS: raise WorkflowError('DEMO_PROFILE_FORBIDDEN')
    return ACTORS[selector]

def trusted(actor):
    if not any(actor is a for a in ACTORS.values()): raise WorkflowError('DEMO_PROFILE_FORBIDDEN')
    actor.require_scope(*SCOPE)

def can(actor, case, action):
    trusted(actor)
    return any(actor is a for a in ACTION_ACTORS.get(case, {}).get(action, ()))

def require_action(actor, case, action):
    if not can(actor, case, action):
        raise WorkflowError('WRONG_APPROVER' if action in {'review','review_evidence'} else 'EXECUTION_ROLE_FORBIDDEN')

def require_surface(actor, surface):
    trusted(actor)
    if surface not in SURFACES[actor.role]: raise WorkflowError('SURFACE_FORBIDDEN')

def project(actor, *, selected=True):
    trusted(actor)
    return Capabilities(actor_id=actor.actor_id, role=actor.role, selected=selected,
        surfaces=list(SURFACES[actor.role]),
        case_actions={c: [a for a in ACTION_ACTORS[c] if selected and can(actor,c,a)] for c in CASES},
        action_roles={c: {a: [i.role for i in roles] for a,roles in actions.items()} for c,actions in ACTION_ACTORS.items()},
        decision_kinds=list(DECISIONS[actor.role]), scenario_ids=list(SCENARIOS[actor.role]),
        automation_save=selected and actor in (AUTOMATION, ENGINEER),
        demo_controls=selected and actor is AUTOMATION)

def route_allowed(actor, path):
    trusted(actor)
    url=urlsplit(path)
    if url.scheme or url.netloc or '%' in url.path or '\\' in path or '..' in url.path: return False
    parts=url.path.rstrip('/').split('/')
    if parts[:2]!=['','control']: return False
    surface=parts[2] if len(parts)>2 else 'overview'
    surface={'portfolio':'overview','automations':'workflows','runs':'operations'}.get(surface,surface)
    if surface not in SURFACES[actor.role]: return False
    if surface=='decisions' and len(parts)>3:
        return 'engineering_evidence' in DECISIONS[actor.role] if parts[3]=='evidence' else 'validation_authorization' in DECISIONS[actor.role]
    return True

def business_case(view):
    """Keep scoped business outcomes, without technical trace identifiers."""
    value=view.model_copy(deep=True)
    for run in value.runs: run.trace_id=None
    for event in value.activity: event.trace_id=None
    return value

def business_snapshot(snapshot, actor):
    """Case facts remain readable; workspace/configuration and trace metadata do not."""
    trusted(actor)
    value=snapshot.model_copy(deep=True)
    if 'workflows' not in SURFACES[actor.role]: value.workflows=[]; value.automations=[]
    for view in [value,value.standard,value.quality,value.autonomous_quality,value.delivery]:
        if not view: continue
        for run in view.runs: run.trace_id=None
        for event in view.activity: event.trace_id=None
    for d in value.decision_summaries:
        if not route_allowed(actor,d.href):
            d.href=f'/control/programs/PRG-A17/cases/{d.change_id}' + ('?tab=options' if d.change_id=='CR-017' else '#decision')
    return value

def decision_queue(snapshot, actor):
    require_surface(actor,'decisions')
    return [d for d in snapshot.decision_summaries if d.kind in DECISIONS[actor.role]]
