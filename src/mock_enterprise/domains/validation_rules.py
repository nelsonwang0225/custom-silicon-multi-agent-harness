"""Computed coverage and scheduling eligibility; no seeded option names in rules."""
from datetime import timedelta

from ..core import at, digest, fail, iso

CONFIG_FIELDS = ('product_id', 'product_revision', 'model_bundle_id', 'device_count',
                 'firmware', 'runtime', 'quantization', 'memory_configuration')
WORKLOAD_FIELDS = ('model_bundle_id', 'context_bins', 'concurrency', 'output_tokens', 'total_suite_minutes')
ACTIONS = ['link_program_plan', 'schedule_validation']


def context(store, actor, change_id):
    change = store.get('engineering.change', change_id, actor)
    target = store.get('engineering.requirement', change['proposed_requirement_revision_id'], actor)
    configuration = store.get('engineering.configuration', target['configuration_id'], actor)
    workload = store.get('engineering.workload', target['workload_profile_id'], actor)
    criteria = store.get('engineering.criteria', target['acceptance_limits_ref'], actor)
    milestone = store.get('planner.milestone', change['milestone_id'], actor)
    order = store.get('erp.order', change['order_id'], actor)
    program = store.get('planner.program', change['program_id'], actor)
    baseline = store.get('engineering.requirement', change['baseline_requirement_revision_id'], actor)
    fail(target['configuration_id'] == change['configuration_id'] == program['configuration_id'] and
         milestone['order_id'] == order['id'] == program['order_id'] and
         baseline['acceptance_limits_ref'] == target['acceptance_limits_ref'] and
         baseline['requirement_id'] == target['requirement_id'] and
         all(order[f] == configuration[f] == program[f] for f in ('product_id', 'product_revision')) and
         workload['model_bundle_id'] == configuration['model_bundle_id'],
         422, 'RESOURCE_INELIGIBLE', 'Inconsistent change applicability.')
    procedures = [p for p in store.list('engineering.procedure', actor)
                  if p['status'] == 'approved' and p['workload_profile_id'] == workload['id']
                  and configuration['id'] in p['supported_configuration_ids']]
    from .standard_change import standard_request
    standard = standard_request(store, actor, change_id)
    if standard:
        # Generic coverage describes the unchanged requirement baseline. Exact
        # requested applicability is checked separately by the standard policy.
        rule = next((r for r in store.list('engineering.standard_rule', actor) if r['id']==standard['routing_rule_id']), None)
        procedure_id = rule['procedure_id'] if rule else standard['procedure_id']
        procedures = [p for p in procedures if p['id'] == procedure_id]
    fail(len(procedures) == 1, 422, 'RESOURCE_INELIGIBLE', 'Exactly one approved applicable procedure is required.')
    procedure = procedures[0]
    policies = [p for p in store.list('engineering.policy', actor)
                if p['status'] == 'approved' and procedure['id'] in p['permitted_procedure_ids']]
    fail(len(policies) == 1, 422, 'RESOURCE_INELIGIBLE', 'Exactly one applicable approval policy is required.')
    fail(procedure['acceptance_limits_ref'] == criteria['id'] and criteria['status'] == 'approved' and
         procedure['suite_minutes'] == workload['total_suite_minutes'] == len(workload['context_bins']) * procedure['per_bin_minutes'],
         422, 'RESOURCE_INELIGIBLE', 'Procedure or criteria is inconsistent.')
    return dict(change=change, target=target, config=configuration, workload=workload,
                criteria=criteria, procedure=procedure, policy=policies[0], milestone=milestone,
                order=order, program=program, baseline=baseline)


def coverage(store, actor, ctx):
    items, evidence = [], []
    for result in store.list('validation.result', actor, program_id=ctx['change']['program_id']):
        reasons = []
        actual_config = store.get('engineering.configuration', result['configuration_id'], actor)
        actual_profile = store.get('engineering.workload', result['workload_profile_id'], actor)
        actual_criteria = store.get('engineering.criteria', result['acceptance_limits_ref'], actor)
        evidence.append([result, actual_config, actual_profile, actual_criteria])
        if result['product_revision'] != ctx['config']['product_revision']:
            reasons.append('WRONG_PRODUCT_REVISION')
        if result['configuration_id'] != ctx['config']['id'] or any(result['configuration_snapshot'][f] != ctx['config'][f] for f in CONFIG_FIELDS):
            reasons.append('WRONG_CONFIGURATION')
        if result['model_bundle_id'] != ctx['config']['model_bundle_id']:
            reasons.append('WRONG_MODEL')
        if result['workload_profile_id'] != ctx['workload']['id'] or any(result['workload_snapshot'][f] != ctx['workload'][f] for f in WORKLOAD_FIELDS):
            reasons.append('WRONG_PROFILE')
        for version, source, snapshot in (
            ('configuration_content_version', actual_config, 'configuration_snapshot'),
            ('workload_profile_content_version', actual_profile, 'workload_snapshot'),
            ('acceptance_criteria_content_version', actual_criteria, 'criteria_snapshot'),
        ):
            if result[version] != source['content_version'] or result[snapshot] != source:
                reasons.append('STALE_EVIDENCE_BINDING')
        if result['acceptance_limits_ref'] != ctx['criteria']['id']:
            reasons.append('WRONG_CRITERIA')
        # Only an immutable, source-owned demo completion may carry a later simulated time.
        from .downstream import completions
        arrivals = completions(store, actor, result_id=result['id'])
        arrived = any(e['result_digest'] == digest(result) and e['completed_at'] == result['completed_at'] for e in arrivals)
        if result['status'] != 'completed' or result['criteria_passed'] is not True or (at(result['completed_at']) > at(store.now) and not arrived):
            reasons.append('NOT_COMPLETED_PASS')
        bins, observed = set(ctx['workload']['context_bins']), result['observed_minutes_by_context_bin']
        if not bins.issubset(result['covered_context_bins']):
            reasons.append('MISSING_CONTEXT_BINS')
        if result['actual_suite_minutes'] < ctx['procedure']['suite_minutes'] or any(observed.get(str(b), 0) < ctx['procedure']['per_bin_minutes'] for b in bins):
            reasons.append('INSUFFICIENT_DURATION')
        if sum(observed.values()) != result['actual_suite_minutes'] or set(map(int, observed)) != set(result['covered_context_bins']):
            reasons.append('INCONSISTENT_OBSERVATION')
        items.append(dict(result=result, satisfies=not reasons, mismatch_reasons=sorted(set(reasons))))
    # Conflicting source observations from a newly recorded campaign remain a gap,
    # even when one observation says pass. Historical unrelated runs are unaffected.
    from .downstream import completions
    for event in completions(store, actor, change_id=ctx['change']['id']):
        primary = next((i for i in items if i['result']['id'] == event['result_id']), None)
        if not primary:
            continue
        r = primary['result']
        conflicts = [i for i in items if i is not primary and
            all(i['result'][k] == r[k] for k in ('configuration_snapshot', 'workload_snapshot', 'criteria_snapshot', 'sample_id')) and
            at(i['result']['completed_at']) >= at(event['started_at']) and
            (i['result']['criteria_passed'] != r['criteria_passed'] or i['result']['status'] != r['status'])]
        if conflicts:
            for item in [primary, *conflicts]:
                item['satisfies'] = False
                item['mismatch_reasons'] = sorted(set(item['mismatch_reasons'] + ['CONFLICTING_RESULT']))
    return dict(synthetic=True, change_id=ctx['change']['id'], items=items,
                coverage_satisfied=any(r['satisfies'] for r in items),
                evidence_set_digest=digest(evidence))


def calculate_option(store, actor, ctx, slot, sample, *, owned_job=None):
    fail(slot['program_id'] == sample['program_id'] == ctx['change']['program_id'], 422, 'RESOURCE_INELIGIBLE', 'Resources must belong to the change program.')
    lab = store.get('validation.lab', slot['lab_id'], actor)
    rate = store.get('erp.rate', slot['rate_id'], actor)
    unit = store.get('manufacturing.unit', sample['unit_id'], actor)
    lot = store.get('manufacturing.lot', unit['source_lot_id'], actor)
    config, procedure, policy = ctx['config'], ctx['procedure'], ctx['policy']
    start = at(slot['starts_at'])
    execution = start + timedelta(minutes=procedure['setup_minutes'])
    end = execution + timedelta(minutes=procedure['suite_minutes'])
    ready = end + timedelta(minutes=procedure['review_minutes'])
    slack = int((at(ctx['milestone']['baseline_at']) - ready).total_seconds() // 60)
    reasons = []
    if config['id'] not in lab['supported_configuration_ids']:
        reasons.append('LAB_CONFIGURATION_UNSUPPORTED')
    if procedure['id'] not in lab['supported_procedure_ids']:
        reasons.append('LAB_PROCEDURE_UNSUPPORTED')
    if sample['configuration_id'] != config['id'] or any(unit[f] != config[f] or lot[f] != config[f] for f in ('product_id', 'product_revision')):
        reasons.append('SAMPLE_CONFIGURATION_MISMATCH')
    if sample['campus'] != lab['campus']:
        reasons.append('CAMPUS_MISMATCH')
    if unit['restrictions'] or lot['restrictions']:
        reasons.append('MANUFACTURING_RESTRICTION')
    if any(not timedelta(0) <= at(store.now) - at(r['updated_at']) <= timedelta(minutes=store.meta['partner_freshness_limit_minutes']) for r in (unit, lot)):
        reasons.append('PARTNER_DATA_STALE')
    if start < at(store.now) or end > at(slot['ends_at']):
        reasons.append('SLOT_TOO_SHORT_OR_PAST')
    if rate['status'] != 'approved' or not at(rate['effective_from']) <= start < end <= at(rate['effective_to']):
        reasons.append('RATE_NOT_EFFECTIVE')
    for resource in (slot, sample):
        available = resource['availability'] == 'available' and resource['reserved_by_job_id'] is None
        owned = owned_job is not None and resource['availability'] == 'reserved' and resource['reserved_by_job_id'] == owned_job
        if not (available or owned):
            reasons.append('RESOURCE_UNAVAILABLE')
    for reservation in store.list('validation.reservation', actor):
        if reservation['job_id'] == owned_job:
            continue
        if reservation['slot_id'] == slot['id'] or reservation['sample_id'] == sample['id'] or (
                reservation['lab_id'] == lab['id'] and at(reservation['starts_at']) < end and start < at(reservation['ends_at'])):
            reasons.append('RESERVATION_CONFLICT')
    approval_reasons = []
    if rate['incremental_cost_cents'] > policy['max_incremental_cost_cents']:
        approval_reasons.append('APPROVAL_POLICY_EXCEEDED')
    if not set(ACTIONS).issubset(policy['permitted_actions']):
        approval_reasons.append('ACTION_OUT_OF_POLICY')
    return dict(slot=slot, lab=lab, sample=sample, unit_id=unit['id'], lot_id=lot['id'],
                configuration_id=config['id'], procedure_id=procedure['id'], policy_id=policy['id'],
                milestone_id=ctx['milestone']['id'], rate=rate, cost_cents=rate['incremental_cost_cents'], currency='USD',
                resource_eligible=not reasons, approval_eligible=not reasons and not approval_reasons,
                eligibility_reasons=sorted(set(reasons)), approval_reasons=approval_reasons,
                meets_deadline=slack >= 0 if not reasons else None,
                timing=dict(lab_start_at=iso(start), execution_start_at=iso(execution), lab_end_at=iso(end),
                            review_ready_at=iso(ready), deadline_slack_minutes=slack) if not reasons else None)
