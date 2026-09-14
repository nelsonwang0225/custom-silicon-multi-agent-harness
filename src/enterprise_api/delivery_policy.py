"""Deterministic delivery gates. This module has no I/O or write authority."""
from datetime import datetime, timedelta, timezone
from .delivery_models import DeliveryAnalysis, DeliveryOption
from .standard_policy import digest


def review_digest(configuration, requirement, workload, criteria, evidence):
    return digest(dict(configuration=configuration, requirement=requirement, workload=workload, criteria=criteria, evidence=evidence))


def technical(c):
    r, cfg, req, work = c.request, c.configuration, c.requirement, c.workload
    reasons = []
    if req['configuration_id'] != cfg['id'] or cfg['id'] != r.configuration_id or req['id'] != r.requirement_revision_id:
        reasons.append('Required Engineering configuration does not match')
    if r.technical_change_id:
        dep = c.technical_dependency or {}
        physical = dep.get('physical', {})
        change = dep.get('change', {})
        binding = physical.get('evidence_binding') or {}
        if change.get('proposed_requirement_revision_id') != req['id'] or binding.get('requirement', {}).get('id') != req['id']:
            reasons.append('CR-017 requirement evidence is not established for this release')
        if physical.get('engineering_status') != 'approved' or physical.get('applicability') != 'confirmed':
            reasons.append('CR-017 technical evidence and separate Engineering review remain pending')
        return ('BLOCKED', reasons) if reasons else ('READY', ['Exact CR-017 evidence and Engineering review are current'])
    if req['status'] != 'approved' or c.criteria['status'] != 'approved':
        reasons.append('Engineering requirement or criteria is not approved')
    clearance = c.clearance
    if not clearance:
        return 'UNKNOWN', reasons + ['Engineering delivery clearance is missing']
    if (clearance.status != 'approved' or clearance.requirement_revision_id != req['id'] or clearance.configuration_id != cfg['id']
            or clearance.acceptance_blockers):
        reasons += ['Engineering clearance is not current and unblocked'] + clearance.acceptance_blockers
    if clearance.review_digest != review_digest(cfg, req, work, c.criteria, c.evidence):
        reasons.append('Engineering review does not bind the current evidence versions')
    if not c.evidence or set(clearance.evidence_ids) != {e['id'] for e in c.evidence}:
        return 'UNKNOWN', reasons + ['Required validation evidence is missing']
    for e in c.evidence:
        exact = (e['configuration_id'] == cfg['id'] and e['configuration_content_version'] == cfg['content_version']
            and e['product_revision'] == cfg['product_revision'] and e['model_bundle_id'] == cfg['model_bundle_id']
            and e['workload_profile_id'] == work['id'] and e['workload_profile_content_version'] == work['content_version']
            and e['acceptance_limits_ref'] == c.criteria['id'] and e['acceptance_criteria_content_version'] == c.criteria['content_version']
            and e['status'] == 'completed' and e['criteria_passed']
            and set(e['covered_context_bins']) == set(work['context_bins'])
            and e['actual_suite_minutes'] >= work['total_suite_minutes']
            and all(e['observed_minutes_by_context_bin'].get(str(b), 0) >= work['total_suite_minutes'] // len(work['context_bins']) for b in work['context_bins']))
        if not exact: reasons.append('Validation result is inapplicable or insufficient: ' + e['id'])
    return ('BLOCKED', reasons) if reasons else ('READY', ['Approved baseline scope, applicable evidence and exact Engineering clearance'])


def analyze(c):
    r = c.request
    tech, technical_reasons = technical(c)
    inventory_reasons = []
    if len({m.id for m in c.material}) != len(c.material) or len({m.lot_id for m in c.material}) != len(c.material):
        inventory_reasons.append('Duplicate material or overlapping lot group')
    lots = {lot['id']: lot for lot in c.lots}
    if set(r.material_ids) != {m.id for m in c.material} or len(r.material_ids) != len(set(r.material_ids)):
        inventory_reasons.append('Material scope is incomplete or repeated')
    totals = dict(physical=0, held=0, allocated=0, mismatch=0, released=0, other=0)
    for m in c.material:
        totals['physical'] += m.physical_quantity
        lot = lots.get(m.lot_id)
        allocations = [a for a in c.allocations if a.material_id == m.id]
        if sum(a.quantity for a in allocations) != m.allocated_quantity or any(a.order_id != m.allocation_order_id for a in allocations):
            inventory_reasons.append('ERP allocation differs from Manufacturing: ' + m.id)
        if not lot:
            inventory_reasons.append('Missing lot provenance: ' + m.lot_id)
        held = m.held_quantity
        allocated = m.allocated_quantity
        # A lot restriction excludes every physical unit, including first-pass passes.
        if not lot or lot.get('restrictions') or m.disposition != 'released':
            totals['held'] += held
            totals['allocated'] += allocated
            totals['other'] += m.physical_quantity - held - allocated
            if m.disposition == 'released' and lot and lot.get('restrictions'):
                inventory_reasons.append('Lot restrictions conflict with material release: ' + m.id)
            continue
        totals['held'] += held
        totals['allocated'] += allocated
        unallocated = m.released_quantity - allocated
        compatible = (m.configuration_id == r.configuration_id and lot['product_id'] == c.configuration['product_id']
            and lot['product_revision'] == c.configuration['product_revision'])
        usable = min(unallocated, m.eligible_unallocated_quantity) if compatible else 0
        totals['released'] += usable
        totals['mismatch'] += unallocated if not compatible else 0
        totals['other'] += m.physical_quantity - held - allocated - usable - (unallocated if not compatible else 0)
    if any(a.material_id not in {m.id for m in c.material} for a in c.allocations):
        inventory_reasons.append('Allocation outside material scope')
    for a in c.allocations:
        order = next((o for o in c.allocation_orders if o['id'] == a.order_id), None)
        if not order or order['quantity'] < sum(x.quantity for x in c.allocations if x.order_id == a.order_id):
            inventory_reasons.append('Allocation obligation is missing or smaller than allocated quantity')
    consistent = not inventory_reasons and totals['physical'] == sum(totals[k] for k in ('held','allocated','mismatch','released','other'))
    eligible = totals['released'] if consistent else 0
    gap = max(0, r.quantity - eligible) if r.quantity is not None else None
    ship = arrival = proposed = None
    timing_status = 'unknown'; timing_reasons = []
    l = c.logistics
    if not r.requested_at: timing_reasons.append('Requested date missing; commercial clarification required')
    if not l or l.milestone_id != r.milestone_id or l.destination != r.destination or l.state != 'confirmed':
        timing_reasons.append('Logistics timing or destination requires confirmation')
        timing_status = 'conditional' if l and l.state == 'conditional' else 'unknown'
    elif all(x is not None for x in (l.material_ready_at, l.preparation_minutes, l.loading_minutes, l.transit_minutes)):
        try:
            material_at = datetime.fromisoformat(l.material_ready_at)
            if material_at.utcoffset() != timedelta(0): raise ValueError('UTC required')
            ship_dt = material_at + timedelta(minutes=l.preparation_minutes+l.loading_minutes)
            arrival_dt = ship_dt + timedelta(minutes=l.transit_minutes)
            iso = lambda x: x.astimezone(timezone.utc).isoformat().replace('+00:00','Z')
            ship, arrival = iso(ship_dt), iso(arrival_dt)
            if r.requested_at:
                earliest = ship_dt if r.date_semantics == 'ship' else arrival_dt
                timing_status = 'supported' if earliest <= datetime.fromisoformat(r.requested_at) else 'late'
                proposed = r.requested_at if timing_status == 'supported' else None
                timing_reasons.append('Source-confirmed preparation, loading and transit in elapsed UTC time')
        except (ValueError, TypeError): timing_reasons.append('Logistics dates are invalid or lack UTC provenance')
    else: timing_reasons.append('Source logistics durations are missing')
    blockers = ([] if tech == 'READY' else technical_reasons) + inventory_reasons
    if not r.quantity: blockers.append('Requested quantity missing')
    if timing_status != 'supported': blockers += timing_reasons or ['Requested timing is not supportable']
    if not eligible: blockers.append('No current eligible unallocated supply')
    if r.quantity and r.quantity != c.order['quantity']: blockers.append('Delivery request quantity differs from the exact order')
    if (r.order_id != c.milestone['order_id'] or r.order_id != c.order['id'] or c.order['product_id'] != c.configuration['product_id']):
        blockers.append('Order, milestone or configuration scope differs')
    allowed = not blockers
    options = []
    quantity = min(eligible, r.quantity) if r.quantity is not None else 0
    if quantity:
        options.append(DeliveryOption(id='partial_commitment', quantity=quantity, remaining_gap=gap, proposed_at=proposed,
            date_semantics=r.date_semantics, executable=allowed, owner=r.commitment_owner, required_role='program_owner',
            prerequisites=['Exact Program Owner commitment approval', 'Customer agreement remains separate'] + blockers,
            effect='Authorize only current supported quantity; remaining demand stays uncommitted. No reallocation or shipment.', affected_obligations=[r.order_id]))
    if totals['allocated']:
        options.append(DeliveryOption(id='allocation_review', quantity=totals['allocated'], remaining_gap=max(0,(gap or 0)-totals['allocated']) if gap is not None else None,
            proposed_at=None, date_semantics=r.date_semantics, executable=False, owner='Supply / Program owner', required_role='separate_supply_owner',
            prerequisites=['Separate exact allocation authorization', 'Protect the existing release obligation'],
            effect='Analysis only: moving these units would reduce supply for another obligation. No allocation executor.', affected_obligations=[a.order_id for a in c.allocations]))
    for future in c.future_supply:
        if future.configuration_id == r.configuration_id:
            options.append(DeliveryOption(id='future_supply', quantity=future.quantity, remaining_gap=max(0,(gap or 0)-future.quantity) if gap is not None else None,
                proposed_at=future.expected_at, date_semantics='expected_material', executable=False, owner='Supply / Logistics', required_role='program_owner',
                prerequisites=future.release_prerequisites+['Receipt, quality release and arrival logistics must be confirmed'],
                effect=f'Source {future.id}: {future.status}; expected material date is not an arrival commitment.', affected_obligations=[r.order_id]))
    return DeliveryAnalysis(technical_readiness=tech,technical_reasons=technical_reasons, physical_total=totals['physical'],held_quantity=totals['held'],
        allocated_quantity=totals['allocated'],configuration_mismatch_quantity=totals['mismatch'],released_unallocated_quantity=totals['released'],
        other_unavailable_quantity=totals['other'],eligible_quantity=eligible,requested_quantity=r.quantity,gap_quantity=gap,
        customer_ready_quantity=quantity if tech=='READY' else 0,future_expected_quantity=sum(f.quantity for f in c.future_supply if f.configuration_id==r.configuration_id),
        inventory_consistent=consistent,inventory_reasons=inventory_reasons,earliest_ship_at=ship,earliest_arrival_at=arrival,proposed_at=proposed,
        timing_status=timing_status,timing_reasons=timing_reasons,full_request_supportable=allowed and gap==0,proposal_allowed=allowed,blockers=blockers,options=options)


def plan_digest(plan):
    return digest({k:v for k,v in plan.items() if k != 'plan_digest'})
