from .core import digest, fail
from .db import SOURCE_MODELS
from .domains.validation_rules import coverage, context


def critical_content(kind, record):
    data = dict(record)
    for field in ("category", "owner", "priority", "next_action", "summary", "inventory_state", "name", "business_unit", "lifecycle", "health"):
        if data.get(field) is None: data.pop(field, None)
    # Optional descriptive fields were added after the first demo generation.
    # Empty defaults must not invalidate previously approved snapshots. Supplied
    # descriptions remain critical content and are bound like all source fields.
    if kind in ('manufacturing.lot', 'manufacturing.unit') and not data.get('hold_details'):
        data.pop('hold_details', None)
    if kind == 'erp.rate':
        for field in ('service_name', 'service_description'):
            if data.get(field) is None:
                data.pop(field, None)
    if kind == 'engineering.document':
        # Absent publication metadata adds no new fact to an existing approval.
        # Populated values remain bound; historical=True remains critical.
        for field in ('title', 'product', 'configuration_id', 'owner_team', 'effective_date', 'superseded_by', 'applicable_workflows'):
            if data.get(field) is None:
                data.pop(field, None)
        if data.get('historical') is False:
            data.pop('historical', None)
    ignored = {'updated_at'} if not kind.startswith('manufacturing.') else set()
    if kind == 'engineering.change':
        ignored |= {'workflow_state', 'record_version', 'current_plan_id'}
    if kind == 'planner.milestone':
        ignored |= {'current_forecast_at', 'forecast_status', 'record_version', 'dependencies'}
    if kind in ('validation.slot', 'validation.sample'):
        ignored |= {'availability', 'availability_version', 'reserved_by_job_id'}
    return {k: v for k, v in data.items() if k not in ignored}


def snapshot(store, actor, kind, record_id):
    fail(kind in SOURCE_MODELS, 422, 'INVALID_SOURCE_SET', 'Unsupported source type.')
    record = store.get(kind, record_id, actor)
    content = critical_content(kind, record)
    return dict(resource_type=kind, resource_id=record_id, content_version=record['content_version'],
                availability_version=record.get('availability_version'), content=content, content_digest=digest(content))


def source_snapshot(store, actor, ctx, option, assessment=None):
    actor = actor.scoped(ctx['change']['program_id'], ctx['change']['customer_id'])
    refs = set()
    context_kinds = dict(change='engineering.change', target='engineering.requirement',
                         baseline='engineering.requirement', config='engineering.configuration',
                         workload='engineering.workload', criteria='engineering.criteria',
                         procedure='engineering.procedure', policy='engineering.policy',
                         milestone='planner.milestone', order='erp.order', program='planner.program')
    for name, kind in context_kinds.items():
        refs.add((kind, ctx[name]['id']))
    for key in ('configuration_id', 'workload_profile_id'):
        kind = 'engineering.configuration' if key == 'configuration_id' else 'engineering.workload'
        refs.add((kind, ctx['baseline'][key]))
    for kind, record_id in (
        ('validation.slot', option['slot']['id']), ('validation.sample', option['sample']['id']),
        ('validation.lab', option['lab']['id']), ('erp.rate', option['rate']['id']),
        ('manufacturing.unit', option['unit_id']), ('manufacturing.lot', option['lot_id']),
        ('engineering.customer', ctx['program']['customer_id']),
        ('engineering.supplier', ctx['program']['supplier_id']),
    ):
        refs.add((kind, record_id))
    # Standard-package documents belong to that distinct request. Installing an
    # unrelated case must not expand CR-017's already-approved critical set.
    # Every pre-existing document and explicit assessment reference stays bound.
    from .domains.standard_change import installed
    scoped_documents = {}
    if installed(store):
        for request in store.list('engineering.standard_request', actor, program_id=ctx['change']['program_id']):
            ids = {request['request_document_id']}
            rule = next((r for r in store.list('engineering.standard_rule', actor) if r['id']==request['routing_rule_id']), None)
            if rule:
                ids.add(rule['document_id'])
                procedure = next((p for p in store.list('engineering.procedure', actor) if p['id']==rule['procedure_id']), None)
                if procedure: ids.add(procedure['document_id'])
            for document_id in ids:
                scoped_documents.setdefault(document_id, set()).add(request['change_id'])
    for doc in store.list('engineering.document', actor, program_id=ctx['change']['program_id']):
        # A quality-only publication must not expand an unrelated change plan's
        # critical set. Explicit assessment references are still bound below.
        if doc.get('applicable_workflows') and 'requirement_change_analysis' not in doc['applicable_workflows']:
            continue
        if doc['id'] not in scoped_documents or ctx['change']['id'] in scoped_documents[doc['id']]:
            refs.add(('engineering.document', doc['id']))
    for result in store.list('validation.result', actor, program_id=ctx['change']['program_id']):
        refs.add(('validation.result', result['id']))
        refs.add(('engineering.configuration', result['configuration_id']))
        refs.add(('engineering.workload', result['workload_profile_id']))
        refs.add(('engineering.criteria', result['acceptance_limits_ref']))
    if assessment:
        for fact in assessment['facts']:
            refs.update((r['resource_type'], r['resource_id']) for r in fact['source_refs'])
    return [snapshot(store, actor, kind, rid) for kind, rid in sorted(refs)]


def expected_sources(snapshots, evidence_digest):
    return dict(records=[{k: r[k] for k in ('resource_type', 'resource_id', 'content_version', 'availability_version')} for r in snapshots],
                evidence_set_digest=evidence_digest)


def check_expected(expected, current):
    def keyed(entries):
        return {(r['resource_type'], r['resource_id']): r for r in entries}
    before, after = keyed(expected['records']), keyed(current['records'])
    fail(len(before) == len(expected['records']) and before.keys() == after.keys(), 422,
         'INVALID_SOURCE_SET', 'The complete applicable source set is required without duplicates or extras.')
    fail(before == after and expected['evidence_set_digest'] == current['evidence_set_digest'], 409,
         'STALE_SOURCE', 'Source versions changed; reassess the plan.')


def check_live(store, actor, plan, *, job=None):
    reservation = store.get('validation.reservation', job['reservation_id'], actor) if job else None
    for prior in plan['source_snapshot']:
        kind, record_id = prior['resource_type'], prior['resource_id']
        current = snapshot(store, actor, kind, record_id)
        fail(current['content_digest'] == prior['content_digest'] and current['content_version'] == prior['content_version'],
             409, 'STALE_SOURCE', 'Critical source content changed; reassessment required.', resource_type=kind, resource_id=record_id)
        if prior['availability_version'] is not None:
            actual = store.get(kind, record_id, actor)
            owned = reservation and ((kind == 'validation.slot' and record_id == reservation['slot_id']) or
                                     (kind == 'validation.sample' and record_id == reservation['sample_id']))
            if owned:
                prefix = 'slot' if kind == 'validation.slot' else 'sample'
                fail(reservation['plan_id'] == plan['id'] and reservation['job_id'] == job['id'] and
                     reservation[f'{prefix}_version_before'] == prior['availability_version'] and
                     actual['availability_version'] == reservation[f'{prefix}_version_after'] and
                     actual['reserved_by_job_id'] == job['id'] and actual['availability'] == 'reserved' and
                     reservation['starts_at'] == plan['timing']['lab_start_at'] and reservation['ends_at'] == plan['timing']['lab_end_at'],
                     409, 'STALE_SOURCE', 'Approved reservation provenance changed.')
            else:
                fail(actual['availability_version'] == prior['availability_version'] and actual['availability'] == 'available' and actual['reserved_by_job_id'] is None,
                     409, 'STALE_SOURCE', 'Resource availability changed after planning.')
    ctx = context(store, actor, plan['change_id'])
    fail(coverage(store, actor, ctx)['evidence_set_digest'] == plan['evidence_set_digest'],
         409, 'STALE_SOURCE', 'Evidence changed after planning.')
    return ctx


def plan_digest(plan):
    return digest({key: value for key, value in plan.items() if key != 'plan_digest'})
