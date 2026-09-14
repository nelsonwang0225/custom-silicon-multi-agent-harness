"""Deterministic comparability and supply math over authoritative source reads."""
from .quality_models import QualityAnalysis
from .standard_policy import digest


def analyze(c):
    o,b=c.observation,c.baseline
    mismatches=[]; missing=[]
    if not b or b.status!='approved': missing.append('Approved baseline unavailable')
    else:
        for key in ('configuration_id','configuration_content_version','product_revision','test_stage','test_program_version','conditions_id','population','equipment_family','sites'):
            a,z=getattr(o,key),getattr(b,key)
            if a is None or z is None or a==[] or z==[]: missing.append(key+' unknown')
            elif a!=z: mismatches.append(key+' differs')
        if b.passed_quantity>b.tested_quantity or b.tested_quantity<o.tested_quantity:
            mismatches.append('Baseline population insufficient or invalid')
    if o.configuration_content_version != c.configuration['content_version'] or o.product_revision != c.configuration['product_revision']:
        mismatches.append('Observed configuration revision differs from current Engineering record')
    comparable='false' if mismatches else 'unknown' if missing else 'true'
    rate=o.passed_quantity*10000//o.tested_quantity
    baseline=b.passed_quantity*10000//b.tested_quantity if b else None
    affected=next(m for m in c.material if m.lot_id==c.exception.lot_id)
    eligible=lambda m: m.eligible_unallocated_quantity if m.disposition=='released' and m.configuration_id==c.exception.configuration_id else 0
    supply=sum(eligible(m) for m in c.material)
    requested=c.order['quantity']; gap=max(0,requested-supply)
    unit_value=c.order.get('planning_unit_value_cents')
    baseline_expected=(o.tested_quantity*b.passed_quantity//b.tested_quantity) if b else None
    first_pass_shortfall=max(0,baseline_expected-o.passed_quantity) if baseline_expected is not None else None
    procedure=c.procedure
    allowed=bool(procedure and procedure.status=='approved' and procedure.configuration_id==c.configuration['id']
        and c.exception.status=='open' and c.lot['id']==o.lot_id==affected.lot_id
        and c.exception.configuration_id==o.configuration_id==affected.configuration_id==c.configuration['id']
        and affected.physical_quantity==o.tested_quantity and affected.first_pass_pass_quantity==o.passed_quantity
        and affected.disposition=='hold' and affected.held_quantity==affected.physical_quantity and 'quality_hold' in c.lot['restrictions']
        and c.lot['product_revision']==c.configuration['product_revision'] and c.lot['product_id']==c.configuration['product_id']
        and len({m.id for m in c.material})==len(c.material) and len({m.lot_id for m in c.material})==len(c.material)
        and affected.expected_milestone_id==c.exception.milestone_id and c.milestone['order_id']==c.exception.order_id
        and c.order['id']==c.exception.order_id and c.milestone['id']==c.exception.milestone_id)
    evidence_status='available' if set(c.exception.evidence_ids)<={e['id'] for e in c.evidence} and c.exception.evidence_ids else 'missing'
    options=[]
    if allowed:
        options.append(dict(id='investigate',scope=c.exception.lot_id,owner=procedure.owner,
            prerequisites=procedure.tasks,expected_effect='Collect evidence for separate Quality review; cause remains unresolved.',
            quantity_impact=0,cost_cents=None,schedule_impact=f'{procedure.investigation_hours} hours planned investigation; no lab reservation.',
            required_role=None))
        options.append(dict(id='released_supply_plan',scope=c.exception.milestone_id,owner=procedure.recovery_owner,
            prerequisites=['Program owner approves exact recovery plan','Separate allocation and commercial authority before shipment changes'],
            expected_effect='Record a recovery task using current released supply as planning context; remaining gap stays open.',
            quantity_impact=min(supply,requested),cost_cents=None,schedule_impact='No baseline, forecast or customer due date change.',required_role='program_owner'))
    allocated=sum(m.allocated_quantity for m in c.material if m.disposition=='released')
    if allocated:
        options.append(dict(id='allocation_tradeoff',scope=c.exception.program_id,owner='Supply / Program owner',
            prerequisites=['Separate allocation approval','Protect existing commitments'],expected_effect='Evaluate already allocated material; unavailable to this milestone.',
            quantity_impact=allocated,cost_cents=None,schedule_impact='Other commitment may be exposed; no allocation path implemented.',required_role='supply_owner'))
    return QualityAnalysis(comparable=comparable,comparison_reasons=mismatches+missing or ['Exact approved baseline conditions match'],
        observed_rate_bps=rate,baseline_rate_bps=baseline,confirmed_degradation=comparable=='true' and rate<baseline,
        affected_physical_quantity=affected.physical_quantity,first_pass_pass_quantity=affected.first_pass_pass_quantity,
        affected_eligible_quantity=eligible(affected),held_quantity=affected.held_quantity,eligible_quantity=supply,
        requested_quantity=requested,gap_quantity=gap,failed_by_site={s:v[0]-v[1] for s,v in o.site_counts.items()},root_cause=o.root_cause,
        planning_unit_value_cents=unit_value,held_value_exposure_cents=affected.held_quantity*unit_value if unit_value is not None else None,
        baseline_expected_pass_quantity=baseline_expected,first_pass_shortfall_quantity=first_pass_shortfall,
        first_pass_shortfall_value_cents=first_pass_shortfall*unit_value if unit_value is not None and first_pass_shortfall is not None else None,
        gap_value_exposure_cents=gap*unit_value if unit_value is not None else None,
        planning_value_basis=c.order.get('planning_value_basis'),
        evidence_status=evidence_status,investigation_allowed=allowed,options=options,
        protected_decisions=['Quality lead: disposition, release and nonstandard retest','Engineering/test owner: technical changes',
            'Supply/program owner: allocation changes','Commercial/program owner: customer commitments'])


def recovery_workstreams(c):
    """Canonical assigned work carried by the exact approved Planner record."""
    from .quality_models import RecoveryWorkstream
    a=analyze(c)
    ranked=sorted(c.observation.site_counts.items(),key=lambda item:item[1][0]-item[1][1],reverse=True)
    suspect,(suspect_tested,suspect_passed)=ranked[0]
    comparison,(comparison_tested,comparison_passed)=ranked[-1]
    released=', '.join(m.lot_id for m in c.material if m.disposition=='released' and m.eligible_unallocated_quantity) or 'No released alternate lot'
    return [
        RecoveryWorkstream(id='containment',source_system='manufacturing',owner='Product Quality / Manufacturing Operations',
            objective=f'Keep {c.exception.lot_id} controlled while the cause is unresolved.',actions=[
                f'Keep all {a.held_quantity} units on Quality hold; do not release, allocate, retest or scrap.',
                f'Preserve {c.observation.id} final-test logs and equipment records.',
                f'Identify adjacent lots processed on the same {suspect} setup.'
            ],completion_criteria='Containment review is documented and Product Quality retains disposition authority.'),
        RecoveryWorkstream(id='site_investigation',source_system='engineering',owner=c.procedure.owner if c.procedure else 'Product / Test Engineering',
            objective=f'Determine why {suspect} produced {suspect_passed}/{suspect_tested} passes versus {comparison} at {comparison_passed}/{comparison_tested}.',actions=[
                'Review failing bins and tests plus socket, contactor, load board, cabling and handler.',
                'Verify calibration, maintenance, power, temperature and timing.',
                f'Reproduce with reference units under {c.observation.test_program_version or "the recorded test program"} and {c.observation.conditions_id or "recorded conditions"}; route persistent failures to failure analysis.'
            ],completion_criteria='Engineering records whether the test setup is qualified and whether failures reproduce.'),
        RecoveryWorkstream(id='controlled_recovery',source_system='manufacturing',owner='Product Quality + Product / Test Engineering',
            objective=f'Define a controlled recovery path without overwriting the original {a.observed_rate_bps/100:g}% first-pass result.',actions=[
                'If a setup issue is confirmed, repair and qualify the setup.',
                f'Define the exact retest population and whether the {a.first_pass_pass_quantity} first-pass passes require rescreening.',
                'Run at most one separately Quality-authorized controlled retest; otherwise continue failure analysis and disposition review.'
            ],completion_criteria='Engineering records setup qualification and Product Quality records released, held or rejected quantities.'),
        RecoveryWorkstream(id='supply_protection',source_system='planner',owner=c.procedure.recovery_owner if c.procedure else 'Program Owner',
            objective=f'Protect the {a.requested_quantity}-unit requirement while the {a.gap_quantity}-unit gap remains open.',actions=[
                f'Use {a.eligible_quantity} eligible units from {released} as planning context.',
                'Identify next-lot supply and capacity; compare quantity, date, cost, risk and owner.',
                'Keep allocation and the ERP commitment unchanged until separately authorized; recalculate after Quality disposition.'
            ],completion_criteria='Planner records the refreshed supply position and any remaining gap after Product Quality disposition.')
    ]


def plan_digest(plan):
    return digest({k:v for k,v in plan.items() if k!='plan_digest'})


STANDARD_QUALITY_ROUTE = 'standard_quality_investigation_handoff'
STANDARD_QUALITY_ACTIONS = ['route_standard_investigation']

def standard_investigation_policy(c):
    """Source/host use the same fail-closed rule; model prose grants no authority."""
    a = analyze(c)
    p = c.procedure
    policy = p.standard_policy if p else None
    destination = c.investigation_destination
    checks = {
        'Isolated QE-011 scope required': c.exception_id == c.exception.id == 'QE-011'
            and c.exception.lot_id == 'LOT-B-219' and c.program_id == c.exception.program_id == 'PRG-A17'
            and c.customer_id == c.exception.customer_id == 'CUST-FML01'
            and len(c.material) == 1 and c.material[0].lot_id == 'LOT-B-219',
        'Known final-test anomaly required': c.exception.exception_type == 'final_test_anomaly'
            and c.observation.test_stage == 'packaged_final_test',
        'Approved scoped procedure and authoritative whole-lot hold required': a.investigation_allowed,
        'Comparable baseline and source evidence required': a.comparable == 'true' and a.evidence_status == 'available',
        'Only standard investigation routing may be requested': c.exception.requested_actions == STANDARD_QUALITY_ACTIONS,
        'No conflicting open exception permitted': not c.conflicting_exception_ids,
        'Approved standard policy required': bool(policy and p.status == 'approved'
            and policy.route == STANDARD_QUALITY_ROUTE and policy.exception_id == c.exception_id
            and policy.lot_id == c.exception.lot_id and policy.exception_type == c.exception.exception_type
            and policy.permitted_actions == STANDARD_QUALITY_ACTIONS
            and policy.approved_tasks == p.tasks),
        'Active approved destination queue and owner required': bool(policy and policy.queue_status == 'active'
            and destination and destination.id=='PROC-QE-B-01' and destination.status=='approved'
            and destination.program_id==c.program_id and destination.customer_id==c.customer_id
            and destination.configuration_id==c.exception.configuration_id
            and policy.queue_id == p.queue_id == destination.queue_id
            and policy.owner == p.owner == destination.owner and p.owner.strip()
            and policy.approved_tasks == destination.tasks),
    }
    return [reason for reason, eligible in checks.items() if not eligible]
