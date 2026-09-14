"""Read projections; no reconciliation writes across domains."""

def plan_view(store, actor, plan):
    state = store.get('engineering.plan_state', plan['id'], actor)
    jobs = store.list('validation.job', actor, plan_id=plan['id'])
    links = store.list('planner.link', actor, plan_id=plan['id'])
    execution = 'scheduled_awaiting_execution' if links else 'lab_scheduled_pending_planner' if jobs else 'not_scheduled'
    return {**plan, 'state': state['state'], 'record_version': state['record_version'],
            'decision_id': state['decision_id'], 'execution_state': execution,
            'job_id': jobs[0]['id'] if jobs else None, 'implementation_link_id': links[0]['id'] if links else None}


def job_view(store, actor, job):
    from .domains.downstream import completions
    events = completions(store, actor, job_id=job['id'])
    return {**job, 'reservation': store.get('validation.reservation', job['reservation_id'], actor),
            'completion': events[0] if events else None}


def link_view(store, actor, link):
    return {**link, 'task': store.get('planner.task', link['task_id'], actor)}
