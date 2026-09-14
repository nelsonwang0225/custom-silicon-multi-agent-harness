"""Quality route in the existing CaseHarness; source-checked claims, no business writes."""
import re
from enterprise_api.quality_models import QualityContext
from enterprise_api.quality_policy import analyze, standard_investigation_policy, STANDARD_QUALITY_ROUTE
from .models import QualityAssessment, QualityClaim, PolicyDecision
from .controls import HarnessError


def claim(c):
    a=analyze(c).model_dump()
    return QualityClaim(exception_id=c.exception_id,lot_id=c.exception.lot_id,
        **{k:a[k] for k in QualityClaim.model_fields if k in a})


async def intake(h):
    e=h.state.event
    async with h.server_factory(h,'coordinator','intake') as server:
        await server.list_tools()
        await server.call_tool('get_program',{'program_id':e.program_id})
        h.intake['program']=h.sources.calls[-1]
        await server.call_tool('get_quality_context',{'exception_id':e.change_id})
        h.intake['quality']=h.sources.calls[-1]
        c=QualityContext.model_validate(h.intake['quality']['data'])
        if (c.exception_id!=e.change_id or c.program_id!=e.program_id or c.customer_id!=e.customer_id
                or c.exception.request_source!=e.source_system or c.exception.requested_by!=e.requested_by
                or not set(e.linked_record_ids)<=h.sources.known_ids):
            raise HarnessError('quality_intake_scope_mismatch')
        h.intake_source_ids=set(server.seen_sources)
        h.state.scope_verified=True


def validate_claim(value,c):
    if value!=claim(c):raise HarnessError('quality_claim_mismatch')


def recovery_recommendation(c):
    """Source-grounded QE-004 action plan used by deterministic verification.

    Live runs author the same four-part plan through the Coordinator contract.
    Every action is advisory and preserves the separate source-system authorities.
    """
    a=analyze(c)
    ranked=sorted(c.observation.site_counts.items(),key=lambda item:item[1][0]-item[1][1],reverse=True)
    suspect,(suspect_tested,suspect_passed)=ranked[0]
    comparison,(comparison_tested,comparison_passed)=ranked[-1]
    conditions=c.observation.conditions_id or 'the unrecorded test conditions'
    released=[m.lot_id for m in c.material if m.disposition=='released' and m.eligible_unallocated_quantity]
    supply_source=', '.join(released) if released else 'currently released alternate lots'
    observed=a.observed_rate_bps/100
    return '\n\n'.join([
        '\n'.join([
            f'1. Contain {c.exception.lot_id}',
            f'Recommendation:\n• Keep all {a.held_quantity} units held, including the {a.first_pass_pass_quantity} first-pass passes. Preserve the {observed:g}% result against the 96% baseline; cause remains open.',
            f'Actions the agents can take:\n• Assemble device results, failing bins, logs, and equipment traceability.\n• Identify adjacent lots tested on {suspect} and prepare the containment evidence packet.',
        ]),
        '\n'.join([
            f'2. Investigate {suspect}',
            f'Recommendation:\n• Prioritize {suspect} ({suspect_passed}/{suspect_tested} passed) against {comparison} ({comparison_passed}/{comparison_tested}). Check the interface path, calibration, maintenance, power, temperature, timing, and {c.observation.test_program_version or "test program"} / {conditions}.',
            'Actions the agents can take:\n• Compare source logs and failure signatures by site and equipment.\n• Route the approved worklist to Product / Test Engineering and track reference-unit reproduction or failure analysis.',
        ]),
        '\n'.join([
            '3. Execute a controlled recovery',
            f'Recommendation:\n• After Engineering and Product Quality approve, qualify the setup and define the exact retest or rescreen population for one Quality-authorized controlled retest. Preserve all original first-pass results.',
            'Actions the agents can take:\n• Draft the repair, qualification, retest, and completion-criteria proposal.\n• Assemble traceability evidence and route it for Engineering and Product Quality authorization; agents cannot authorize retest or release.',
        ]),
        '\n'.join([
            f'4. Protect {c.exception.milestone_id}',
            f'Recommendation:\n• Plan with {a.eligible_quantity} eligible units from {supply_source} against the {a.requested_quantity}-unit requirement. Keep the {a.gap_quantity}-unit gap, allocation, and ERP commitment unchanged pending separate authority.',
            'Actions the agents can take:\n• Compare next-lot and capacity options by quantity, date, cost, risk, and owner.\n• After Program Owner approval, create the Planner recovery task and recalculate the gap after Quality disposition.',
        ]),
    ])


def validate_recovery_recommendation(text,c):
    if c.exception_id!='QE-004':return
    a=analyze(c); lower=text.lower()
    hotspot=max(c.observation.site_counts,key=lambda site:c.observation.site_counts[site][0]-c.observation.site_counts[site][1])
    required=(
        '1. contain',c.exception.lot_id.lower(),'2. investigate',hotspot.lower(),
        '3. execute a controlled recovery','4. protect',c.exception.milestone_id.lower(),
        str(a.held_quantity),str(a.eligible_quantity),str(a.requested_quantity),str(a.gap_quantity),
        'quality-authorized','erp commitment',
    )
    if any(value not in lower for value in required):
        raise HarnessError('quality_recommendation_incomplete')


def restrained_prose(output,c):
    # Defense in depth beside typed claims and exact source facts; never a semantic proof.
    from .sources import canonical
    text=canonical(output.model_dump())
    for sentence in re.split(r'[.!?\\\n]',text):
        forbidden=r'(?:tester|equipment|silicon|site) (?:caused|causes|is defective)|(?:lot|material) (?:can ship|is shippable|was released)|delivery will miss|(?:allocation|commitment|disposition) (?:was|has been) changed'
        if re.search(forbidden,sentence,re.I) and not re.search(r'\b(not|no|never|cannot|hypothesis|unproven|unsupported)\b',sentence,re.I):
            raise HarnessError('unsupported_quality_claim')


def validate_quality_assessment(output,registry):
    if not isinstance(output,QualityAssessment):return
    if registry.state.workflow_id!='yield_exception_recovery':raise HarnessError('quality_route_required')
    call=registry.get(output.context_source_id)
    if call['tool']!='get_quality_context' or call['arguments'].get('exception_id')!=registry.state.event.change_id:
        raise HarnessError('quality_context_mismatch')
    c=QualityContext.model_validate(call['data']);validate_claim(output.quality,c);restrained_prose(output,c)


def policy(state,registry):
    call=registry.latest('get_quality_context',exception_id=state.event.change_id)
    roles={r.specialist for r in state.completed_assessments if isinstance(r.assessment,QualityAssessment)}
    required={'manufacturing','validation_evidence','program_commercial'}
    if state.event.change_id == 'QE-011':required.add('change_impact')
    if not call or not required<=roles or state.triage.classified_change_type!='quality_exception':
        return PolicyDecision(policy_path='escalation_required',rule='quality_analysis_incomplete',
            reasons=['Scoped assessments are required from: '+', '.join(sorted(required))+'.'],source_ids=[])
    c=QualityContext.model_validate(call['data']);a=analyze(c)
    if c.exception_id == 'QE-011':
        reasons = standard_investigation_policy(c)
        return PolicyDecision(policy_path='escalation_required' if reasons else 'touchless_eligible',
            rule=STANDARD_QUALITY_ROUTE, quality_context_digest=c.context_digest, source_ids=[call['source_id']],
            reasons=reasons or ['Approved standard investigation routing only; no human approval required for this handoff. Material remains held; root cause unresolved and commitments unchanged.'])
    return PolicyDecision(policy_path='human_review_required' if a.investigation_allowed else 'escalation_required',
        rule='quality_recovery_v1',quality_context_digest=c.context_digest,source_ids=[call['source_id']],
        reasons=['Only standard investigation routing is pre-authorized. Program Owner must review the exact recovery task plan; held material, allocation and commitments remain governed.'] if a.investigation_allowed else ['Approved investigation scope missing or inconsistent; no handoff.'])


def validate_quality_final(output,registry,state):
    if state.workflow_id!='yield_exception_recovery':
        if output.quality is not None:raise HarnessError('quality_route_required')
        return
    call=registry.latest('get_quality_context',exception_id=state.event.change_id)
    if not call:
        if output.quality is not None:raise HarnessError('quality_context_missing')
        return
    c=QualityContext.model_validate(call['data'])
    validate_claim(output.quality,c);restrained_prose(output,c);validate_recovery_recommendation(output.recommended_next_step,c)
    if output.classified_change_type!='quality_exception' and output.policy_path!='escalation_required':raise HarnessError('quality_classification_mismatch')


_SHARED='''This is the connected quality_exception route. The host supplies the verified get_quality_context intake and calculator receipt. Reuse it for shared context; independently confirm the source facts relevant to your domain using scoped read tools. Call get_quality_context again only for a concrete need to refresh the complete cross-system context. It provides authoritative source records and an analysis object calculated by ordinary source code. Copy calculated comparison, rate and quantity fields into quality; never substitute arithmetic from prose. quality.exception_id and lot_id come from the source. release_authorized=false, allocation_authorized=false, commitment_changed=false. A whole held lot contributes zero eligible units regardless of first-pass passes. Baseline differences or missing conditions mean false/unknown comparability, never confirmed degradation. Site concentration is correlation only. root_cause remains null unless the Manufacturing observation establishes it. Historical validation evidence is not lot release evidence. Missing evidence remains missing. Never claim the tester caused failures, silicon is defective, delivery will miss, or that a held lot can ship from correlation or shortage alone. Do not approve or execute, allocate inventory, authorize retests, release holds or change commitments. Every factual finding needs exact SourceFacts and receipts. Preserve unknowns, sources and separate human authorities.'''
INSTRUCTIONS={
 'coordinator':_SHARED+''' You remain the Program Coordinator in the existing lifecycle. Classify quality_exception. Delegate Manufacturing to validate the alert, lot/conditions/hold and material; Validation & Evidence to assess historical evidence, approved procedure and unresolved cause; Program / Commercial to assess milestone/demand and released supply options. These independent reads can run in parallel. Engineering specialist is optional only for a concrete unresolved configuration issue. Reconcile exact source facts; unknown root cause is an open question, not a blocker to a standard investigation package. Respect binding_policy_decision exactly. Final available_options=[] because that schema represents lab scheduling; the quality recovery options are in the host-calculated source analysis. Include every specialist, confirmed facts and required unresolved questions. Include quality with exact calculated claims. business_actions_executed=false; the separate host may route and verify the standard investigation after this validated analysis. QE-004 recovery plans require human review. For QE-004, recommended_next_step is the complete editable agent recommendation and MUST contain exactly four numbered plain-English sections with these headings: "1. Contain <lot_id>", "2. Investigate <highest-failure site>", "3. Execute a controlled recovery", and "4. Protect <milestone_id>". Under every heading, use exactly two short subsections: "Recommendation:" with one or two bullet points, then "Actions the agents can take:" with no more than two bullet points. Keep each bullet to one sentence and describe only actions the agents can actually perform: read and compare records, assemble evidence, draft or route a governed proposal, create an already-approved Planner task, and track status. Use exact source values for the held lot, per-site passed/tested counts, configuration, test program, conditions, first-pass rate, first-pass passes, eligible released supply, requested quantity and remaining gap. In section 1, preserve records, check adjacent lots and keep the whole lot held. In section 2, name the failing-bin/test review; test interface path (socket, contactor, load board, cabling and handler); calibration/maintenance; power, temperature and timing; exact program/conditions; reference-unit reproduction; and failure analysis when failures persist. In section 3, make repair, setup qualification, exact retest population, one Quality-authorized controlled retest, original first-pass-result preservation, rescreen decision and completion criteria conditional on Engineering and Product Quality authority. In section 4, name the released supply lot(s), planning quantity, full requirement, open gap, next-lot/capacity work and quantity/date/cost/risk/owner comparison. State that allocation and the ERP commitment require separate authority and that the gap is recalculated after Quality disposition. These are recommended downstream actions, not completed or authorized actions. Use "Quality-authorized" exactly. For QE-011 the binding standard-quality policy may authorize only investigation routing without a human decision; if ineligible, escalate. Do not request a recovery proposal for eligible QE-011. Keep held material and customer commitment unchanged.''',
 'manufacturing':_SHARED+''' You are the existing Manufacturing Specialist. Read get_manufacturing_lot for the affected lot and referenced alternate material lots. Establish exact lot, stage, denominator, test program, site/equipment, conditions, population and baseline comparison; material scope and hold state. Cite failures by site as correlation. Return QualityAssessment.''',
 'validation_evidence':_SHARED+''' You are the existing Validation & Evidence Specialist. Use get_configuration and get_validation_result for the named existing evidence. Establish approved Engineering investigation procedure/tasks/owner and applicability from the shared authoritative context, historical Validation evidence and its limits. Do not request missing evidence IDs as if established. Preserve unresolved cause and do not grant nonstandard retest or release authority. Return QualityAssessment.''',
 'program_commercial':_SHARED+''' You are the existing Program / Commercial Specialist. Read get_program_milestone and get_customer_order for the source-linked IDs. Establish exact Planner milestone and ERP order quantity/date, affected lot contribution, released/unallocated eligible supply and gap. Compare source-backed recovery options with owner, prerequisites, timing, quantity, cost unknowns and separate authority. No allocation or commitment change is performed. Return QualityAssessment.''',
 'change_impact':_SHARED+''' You are the existing Change Impact Specialist. For QE-011 independently read get_configuration for the source-linked Engineering configuration. Check its identity, revision and scope against the exception and approved investigation procedure in the verified intake. Establish which hardware/software scope is affected and whether the requested_actions are only standard investigation routing or actually request a technical change. Cite exact facts for the configuration and procedure binding. Do not invent a requirement change, acceptance criteria, root cause or authorization. For other quality cases participate only for a concrete unresolved Engineering scope question. Return QualityAssessment.''',
}

INSTRUCTIONS['coordinator'] += ''' For QE-011 specifically, the opening requires all four existing specialists: also delegate Change Impact to independently verify the affected Engineering configuration and the procedure's exact scope, and distinguish investigation routing from a technical change. This is independent of Manufacturing's lot/hold check, Validation's evidence check and Program's supply exposure check, so request all four in parallel with separate concrete questions. You own triage, reconciliation and final synthesis; include the Change Impact findings in both review and the final package. Missing or failed required work must remain incomplete, never an invented successful assessment.'''
