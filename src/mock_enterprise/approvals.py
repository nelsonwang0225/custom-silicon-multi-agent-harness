from .core import IDENTITIES, fail
from .snapshots import plan_digest


def approved_plan(store, actor, plan_id, approval_id):
    plan = store.get('engineering.plan', plan_id, actor)
    approval = store.get('engineering.decision', approval_id, actor)
    state = store.get('engineering.plan_state', plan_id, actor)
    authorized_signer = any(i.id == approval['signer_identity'] and i.role == 'engineer'
                            and (plan['program_id'], plan['customer_id']) in i.scopes
                            for i in IDENTITIES.values())
    fail(approval['decision'] == 'approve' and state['state'] == 'approved' and state['decision_id'] == approval_id and
         approval['plan_id'] == plan_id and approval['plan_version'] == plan['plan_version'] and
         approval['plan_digest'] == plan['plan_digest'] == plan_digest(plan) and
         approval['signer_role'] == 'engineer' and authorized_signer and
         all(approval[k] == plan[k] for k in ('customer_id', 'program_id', 'change_id', 'policy_id', 'cost_cents',
                                            'permitted_actions', 'source_snapshot', 'configuration_id', 'sample_id', 'slot_id', 'milestone_id')),
         403, 'APPROVAL_REQUIRED', 'A matching server-recorded engineer approval is required.')
    return plan, approval
