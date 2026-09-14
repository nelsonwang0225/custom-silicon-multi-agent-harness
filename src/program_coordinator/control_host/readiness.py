"""Operator-only observations. No model requests, writes or new business authority."""
from program_investigator.config import MODEL, PROJECT, InvestigatorError, load_key


def model_configuration():
    # Use the runtime's exact authorized loader. Return presence, never the value.
    try:
        key = load_key(PROJECT / '.env.local')
        configured = bool(key)
        del key
    except InvestigatorError:
        configured = False
    return {'model': MODEL, 'credential_present': configured,
            'status': 'configured' if configured else 'unavailable',
            'connectivity': 'not_checked', 'paid_call_made': False}


def observe(host):
    with host.store.transaction() as data:
        running = [{'run_id': r.run_id, 'case_id': r.case_id, 'status': r.status}
                   for r in data.runs.values() if r.status == 'running'
                   and (r.customer_id, r.program_id) == ('CUST-FML01', 'PRG-A17')]
    concierge = getattr(host, 'concierge', None)
    model = model_configuration() if host.mode == 'live_model' else {
        'model': None, 'credential_present': False, 'status': 'deterministic_test',
        'connectivity': 'not_checked', 'paid_call_made': False}
    return {'mode': host.mode, 'case_runtime_modes': {c:host.runtime_mode(c) for c in ('CR-017','CR-019','QE-004','DR-009','QE-011')}, 'model_configuration': model,
            'runtime_invocable': callable(host.investigate),
            'max_concurrent_workflow_runs': host.max_concurrent_workflow_runs,
            'concierge_route_available': concierge is not None and callable(concierge.manager),
            'active_workflows': running,
            'active_host_tasks': sum(not t.done() for t in host.tasks),
            'active_concierge_turns': sum(not t.done() for t in concierge.tasks.values()) if concierge else 0,
            # Saved generic configurations never install workers. This one-shot
            # demo path exists only when explicit demo management is enabled.
            'background_execution': {'schedulers': 'not_installed', 'event_listeners': 'not_installed',
                                     'condition_evaluators': 'not_installed'},
            'autonomous_opening': host.autonomous.status().model_dump(mode='json') if getattr(host,'autonomous',None) else None}
