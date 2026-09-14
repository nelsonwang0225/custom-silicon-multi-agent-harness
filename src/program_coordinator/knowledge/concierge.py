"""Explanatory Concierge discovery through the same bounded profile/verification boundary."""
from ..control_host.access import project
from ..control_host.concierge_models import Card, Link
from ..control_host.concierge_reads import grounded_cards, views
from starlette.concurrency import run_in_threadpool
from .integration import KnowledgeContext, SpecialistKnowledge, ROLE_PROFILES

async def explain_knowledge(host,turn,route,scope,*,selected_actor,snapshot,case):
    if 'knowledge' not in project(selected_actor).surfaces:
        turn.text='Knowledge documents are not available to this demo identity. Current case facts remain available.'
        return
    profile=route.knowledge_profile or {'QE-004':'MANUFACTURING_QUALITY','CR-017':'VALIDATION_EVIDENCE',
        'CR-019':'PROGRAM_COMMERCIAL','DR-009':'PROGRAM_COMMERCIAL'}.get(case)
    if not profile:
        turn.text='Specify whether you need engineering, validation, quality, or program policy knowledge.'
        return
    role=next(r for r,p in ROLE_PROFILES.items() if p==profile)
    quality = None
    if case == 'QE-004' and snapshot:
        view = views(snapshot)[case]
        if view and view.source_available:
            quality = view.context
    context=SpecialistKnowledge(KnowledgeContext(host.knowledge,selected_actor),role,case_id=case,
        session_id=turn.session_id,invocation_id=turn.message_id,
        configuration_id=quality.exception.configuration_id if quality else None,
        product=quality.configuration.get('product_id') if quality else None)
    question = turn.user_text.casefold()
    historical = 'histor' in question or 'prior' in question or (
        profile == 'MANUFACTURING_QUALITY' and 'site' in question and any(w in question for w in ('cause', 'concentration', 'concentrated')))
    found=await context.search(turn.user_text,'Requested procedural explanation; current state and host authority remain separate.',
        include_historical=historical)
    turn.telemetry.service_calls.append('KnowledgeService.search_knowledge:'+profile)
    evidence=[]
    for result in found.get('results',[])[:3]:
        v=await context.verify(result['chunk_id'])
        if not v['verified']: continue
        from ..models import KnowledgeEvidence
        e=KnowledgeEvidence.model_validate(v['knowledge_evidence']); evidence.append(e)
        turn.cards.append(Card(kind='evidence',knowledge_chunk_id=e.chunk_id,title='Knowledge evidence · '+result['title'],facts=[
            ('Source',e.document_id+' · v'+e.document_version),('Section',e.section or 'Not recorded'),
            ('Status',e.approval_status),('Retrieval profile',e.profile),
            ('Verification','Exact source verified'),('Use','Historical guidance' if e.historical else 'Approved procedural evidence'),
            ('Passage (source text)',result['passage'][:1000])],links=[
            Link(label='Open exact document',href='/control/knowledge?document='+e.document_id)]))
    await context.validate(evidence)
    await context.record_usage(evidence)
    if case:
        cards=await run_in_threadpool(grounded_cards,host,snapshot,case,'status')
        turn.cards=[*cards[:2],*turn.cards]
    turn.text=('Verified knowledge passages are shown with current source facts. Documents explain procedure; they do not change holds, quantities or approval authority.'
        if evidence else 'No eligible, verified knowledge evidence was found. The procedure remains unknown from retrieval; no policy or business conclusion was inferred.')
    if quality:
        held = next((m for m in quality.material if m.lot_id == quality.exception.lot_id and m.disposition == 'hold'), None)
        if held:
            turn.text += (f' Manufacturing currently records {held.lot_id} on HOLD: '
                f'{held.first_pass_pass_quantity} first-pass passing units remain unavailable while held. '
                'Human Quality authority is required for disposition.')
        if quality.observation.root_cause is None:
            turn.text += ' QE-004 root cause remains unresolved. Test-site concentration and historical precedent do not establish causality.'
    turn.telemetry.service_calls.append('KnowledgeService.verify')

def visible_cards(host,cards,actor):
    """Recheck cached explanatory evidence on read; no stale access through chat history."""
    visible=[]
    for card in cards:
        cid=getattr(card,'knowledge_chunk_id',None)
        if cid:
            try:
                if not host.knowledge.verify(actor,cid).verified:continue
            except Exception:continue
        visible.append(card)
    return visible
