"""Delivery analysis in the existing CaseHarness, with source-verified typed claims."""
import re
from enterprise_api.delivery_models import DeliveryContext
from enterprise_api.delivery_policy import analyze
from .models import DeliveryClaim, DeliveryAssessment, PolicyDecision
from .controls import HarnessError


def claim(c):
    a=analyze(c).model_dump()
    return DeliveryClaim(delivery_id=c.delivery_id,order_id=c.request.order_id,
        committed_quantity=c.commitment.quantity if c.commitment else 0,customer_agreement=c.request.customer_agreement,
        **{k:a[k] for k in DeliveryClaim.model_fields if k in a})


async def intake(h):
    e=h.state.event
    async with h.server_factory(h,'coordinator','intake') as server:
        await server.list_tools()
        await server.call_tool('get_program',{'program_id':e.program_id});h.intake['program']=h.sources.calls[-1]
        await server.call_tool('get_delivery_context',{'delivery_id':e.change_id});h.intake['delivery']=h.sources.calls[-1]
        c=DeliveryContext.model_validate(h.intake['delivery']['data'])
        if (c.delivery_id!=e.change_id or c.program_id!=e.program_id or c.customer_id!=e.customer_id
            or c.request.request_source!=e.source_system or c.request.requested_by!=e.requested_by
            or not set(e.linked_record_ids)<=h.sources.known_ids):raise HarnessError('delivery_intake_scope_mismatch')
        h.intake_source_ids=set(server.seen_sources);h.state.scope_verified=True


def validate_claim(value,c):
    if value!=claim(c):raise HarnessError('delivery_claim_mismatch')


def restrained(output):
    from .sources import canonical
    for sentence in re.split(r'[.!?\\\n]',canonical(output.model_dump())):
        bad=r'customer (?:accepted|agreed to) (?:split|partial) delivery|(?:held lot|held material) (?:can ship|is available)|(?:future receipt|future supply) is guaranteed|(?:we|agent) (?:committed|reallocated)|1000 (?:units are|deliverable)'
        if re.search(bad,sentence,re.I) and not re.search(r'\b(not|no|never|cannot|unsupported)\b',sentence,re.I):raise HarnessError('unsupported_delivery_claim')


def validate_delivery_assessment(output,registry):
    if not isinstance(output,DeliveryAssessment):return
    if registry.state.workflow_id!='delivery_readiness':raise HarnessError('delivery_route_required')
    call=registry.get(output.context_source_id)
    if call['tool']!='get_delivery_context' or call['arguments'].get('delivery_id')!=registry.state.event.change_id:raise HarnessError('delivery_context_mismatch')
    validate_claim(output.delivery,DeliveryContext.model_validate(call['data']));restrained(output)


def policy(state,registry):
    call=registry.latest('get_delivery_context',delivery_id=state.event.change_id)
    roles={r.specialist for r in state.completed_assessments if isinstance(r.assessment,DeliveryAssessment)}
    if not call or not {'manufacturing','validation_evidence','program_commercial'}<=roles or state.triage.classified_change_type!='delivery_readiness':
        return PolicyDecision(policy_path='escalation_required',rule='delivery_analysis_incomplete',reasons=['Exact scoped commercial, material and technical evidence is required.'],source_ids=[])
    c=DeliveryContext.model_validate(call['data']);a=analyze(c)
    return PolicyDecision(policy_path='human_review_required' if a.proposal_allowed else 'escalation_required',rule='delivery_commitment_v1',
        delivery_context_digest=c.context_digest,source_ids=[call['source_id']],reasons=['Only an exact Program Owner decision may authorize an ERP commitment and Planner link; no reallocation, shipment or customer acceptance.'] if a.proposal_allowed else a.blockers)


def validate_delivery_final(output,registry,state):
    if state.workflow_id!='delivery_readiness':
        if output.delivery is not None:raise HarnessError('delivery_route_required')
        return
    call=registry.latest('get_delivery_context',delivery_id=state.event.change_id)
    if not call:
        if output.delivery is not None:raise HarnessError('delivery_context_missing')
        return
    validate_claim(output.delivery,DeliveryContext.model_validate(call['data']));restrained(output)
    if output.classified_change_type!='delivery_readiness' and output.policy_path!='escalation_required':raise HarnessError('delivery_classification_mismatch')


_SHARED='''This is the connected delivery_readiness route. Reuse the verified get_delivery_context intake and deterministic calculator receipt. Independently confirm facts relevant to your domain through existing scoped read tools. Return exact calculated values in delivery, never model arithmetic. Physical, held, allocated, eligible, technically ready, committed and delivered are different quantities. Held material and other allocations are excluded. Future expected material is never current supply or guaranteed arrival. Technical readiness requires applicable evidence and exact Engineering review, separately from supply. Respect the request's ship versus arrival semantics and source logistics durations. Missing quantity/date/logistics remains unknown and blocks a commitment. Preserve the existing order-level original date separately from the delivery-release commitment. No model can approve or execute, promise future stock, reallocate, release material, change validation or assert customer agreement. Every factual finding needs exact source facts/receipts. Copy delivery from calculated claims; commitment_changed=false and allocation_authorized=false describe this read-only analysis. Current committed_quantity may reflect an existing ERP record; customer_agreement is separate. Customer technical acceptance is also separate from commercial commitment. Do not claim customer accepted split delivery without a separate source record.'''
INSTRUCTIONS={
 'coordinator':_SHARED+''' You remain Program Coordinator. Classify delivery_readiness; delegate Manufacturing, Validation & Evidence and Program/Commercial. During triage, missing_information means absent or conflicting request identity/scope that prevents those investigations. A known unfilled remainder or absence of a full-order supply/date plan is the subject of this analysis, not missing intake. Preserve that remainder as an open risk/question while assessing any source-supported partial proposal. Independent domain reads can start in parallel; do not make Program/Commercial wait merely because final synthesis will combine its evidence with other domains. Missing inputs needed to establish the exact proposed quantity, destination or ship/arrival timing still block that proposal. Never invent support for the remainder, infer full delivery, or bypass a source technical/timing gate. Engineering is optional only for a specific unresolved configuration question. Respect binding_policy_decision. Unknowns and no supportable full-delivery plan are valid outcomes. Final available_options=[] because that schema is for lab scheduling; delivery options are in the source analysis. Include all specialist findings and required unresolved questions, exact delivery claims, business_actions_executed=false. The separate host may draft the one executable partial_commitment option, but never execute before Program Owner approval. Blocked technical/timing gates require escalation, not a fabricated commitment.''',
 'manufacturing':_SHARED+''' You are the existing Manufacturing specialist. Read each referenced lot, verify shared QE-004 restrictions and non-overlapping material groups. Confirm the ERP allocation ledger against Manufacturing quantities. Do not generalize or double-count material. Return DeliveryAssessment.''',
 'validation_evidence':_SHARED+''' You are the existing Validation & Evidence specialist. Read the required Engineering configuration and available Validation results. Use the exact Engineering clearance and optional CR-017 physical/evidence-review source context to distinguish READY/BLOCKED/CONDITIONAL/UNKNOWN. Do not infer READY from inventory or a scheduled test. Return DeliveryAssessment.''',
 'program_commercial':_SHARED+''' You are the existing Program / Commercial specialist. Read the exact order and Planner milestone. Establish order line, quantity, requested ship/arrival date, destination, logistics, existing allocation obligation and current release commitment. Compare partial commitment, analysis-only allocation review and future supply only if sourced. No unsupported costs/dates. Return DeliveryAssessment.''',
 'change_impact':_SHARED+''' You are the existing Change Impact specialist for a concrete requirement/configuration compatibility question. Return DeliveryAssessment.''',
}
