"""Session-scoped conversational adapter over existing host services.

Action capabilities remain bounded and process-local. Sanitized visible history
is retained separately in the existing host metadata index for Operations.
No source record store, model conversation trace, private reasoning or generic tools.
"""
from ..application.observability import retain_turn, retain_confirmation
import asyncio
import re
import time
from dataclasses import dataclass
from uuid import uuid4
from fastapi import Request
from starlette.concurrency import run_in_threadpool
from pydantic import ValidationError
from ..application.automations import AutomationInput, CreateAutomation, ScheduleTrigger, EventTrigger, trigger_summary
from ..application.models import WorkflowError, now_utc
from ..application.execution_models import SourceReadFailure, SourceFailure
from ..application.contracts import digest
from .models import StartRequest
from .concierge_models import ChatRequest, Confirmation, Turn, Card, Link, Route
from .concierge_reads import CASES, CASE_ROOT, resolve, views, all_runs, case_link, source_link, fields, words, grounded_cards, run_card
from .concierge_runtime import live_manager
from .access import project, route_allowed, business_snapshot
from urllib.parse import urlsplit

async def unavailable_manager(*args):
    raise WorkflowError('CHAT_MODEL_NOT_CONFIGURED')

@dataclass
class PendingAction:
    session_id: str
    actor_id: str
    context: str
    operation: str
    body: dict
    created: float

class Concierge:
    def __init__(self, host, *, manager=None):
        self.host=host
        self.manager=manager or (live_manager if host and host.mode=='live_model' else unavailable_manager)
        self.session_actors={}
        self.turns={}
        self.tasks={}
        self.actions={}
        self.confirm_lock=asyncio.Lock()
        self.receipts={}

    def session_access(self, session, actor, *, create=False):
        owner=self.session_actors.get(session)
        if owner is None and self.host:
            with self.host.store.transaction() as data:
                previous=data.concierge_sessions.get(session)
                if previous:
                    if previous.owner_actor_id != actor.actor_id: raise WorkflowError("CHAT_SESSION_FORBIDDEN")
                    owner=previous.owner_actor_id
        if owner is not None and owner != actor.actor_id: raise WorkflowError("CHAT_SESSION_FORBIDDEN")
        if owner is None and not create: raise WorkflowError("CHAT_SESSION_EXPIRED")
        if create: self.session_actors[session]=actor.actor_id

    def get(self, session, message):
        turn=self.turns.get((session,message))
        if not turn: raise WorkflowError('CHAT_SESSION_EXPIRED')
        return turn

    def visible_turn(self,turn,actor):
        from ..knowledge.concierge import visible_cards
        value=turn.model_copy(deep=True)
        value.cards=visible_cards(self.host,value.cards,actor)
        if len(value.cards)!=len(turn.cards):value.text+=' Some knowledge evidence is no longer available or its source changed.'
        return value

    def prune(self):
        # Bounded session memory; explicit restart/expiry invalidates all old tokens.
        expired=[key for key,a in self.actions.items() if time.monotonic()-a.created>1800]
        for key in expired:self.actions.pop(key,None)
        while len(self.turns)>=256:
            key=next((k for k,v in self.turns.items() if v.status!='running'),None)
            if key is None: raise WorkflowError('CHAT_BUSY')
            self.turns.pop(key);self.receipts.pop(key,None)

    async def start(self, body, request, invoke):
        selected=self.actor(request)
        self.session_access(body.session_id, selected, create=True)
        if not route_allowed(selected,body.context): raise WorkflowError("SURFACE_FORBIDDEN")
        context_parts=urlsplit(body.context).path.rstrip('/').split('/')
        if context_parts[2:4]==['operations','sessions']:
            if len(context_parts)!=5: raise WorkflowError('CHAT_SCOPE_UNAVAILABLE')
            self.session_access(context_parts[4],selected)
        key=(body.session_id,body.message_id)
        fingerprint=digest([body.model_dump(mode='json'),request.headers.get('x-stratos-demo-profile')])
        if key in self.turns:
            if self.receipts[key]!=fingerprint: raise WorkflowError('CHAT_MESSAGE_CONFLICT')
            return await run_in_threadpool(self.visible_turn,self.turns[key],selected)
        if any(t.session_id==body.session_id and t.status=='running' for t in self.turns.values()):raise WorkflowError('CHAT_BUSY')
        if sum(t.status=='running' for t in self.turns.values())>=4:raise WorkflowError('CHAT_BUSY')
        if not body.text.strip(): raise WorkflowError('CHAT_MESSAGE_EMPTY')
        scope=await run_in_threadpool(resolve,self.host,body.context)
        scope['capabilities']=project(selected, selected=request.headers.get('x-stratos-demo-profile') is not None).model_dump(mode='json')
        self.prune()
        turn=Turn(actor_id=selected.actor_id,session_id=body.session_id,message_id=body.message_id,context=body.context,user_text=body.text,created_at=now_utc())
        self.turns[key]=turn;self.receipts[key]=fingerprint
        task=asyncio.create_task(self.respond(turn,scope,request,invoke))
        self.tasks[key]=task
        task.add_done_callback(lambda _:self.tasks.pop(key,None))
        return turn

    async def respond(self, turn, scope, request, invoke):
        started=time.monotonic()
        try:
            history=[{'user':v.user_text,'reply':v.text,'case_ids':[c.title.split(' · ')[0] for c in v.cards if c.kind=='status']}
                     for v in self.turns.values() if v.session_id==turn.session_id and v.message_id!=turn.message_id
                     and v.context==turn.context and v.status=='completed'][-4:]
            turn.telemetry.model_calls=1
            route,telemetry=await asyncio.wait_for(self.manager(self.host.config,turn.user_text,scope,history),timeout=min(90,self.host.config.model_timeout_seconds))
            route=Route.model_validate(route)
            turn.telemetry=telemetry
            turn.intent=route.intent
            await self.dispatch(turn,route,scope,request,invoke)
            self.filter_links(turn.cards,self.actor(request))
            turn.status='completed'
        except asyncio.CancelledError:
            turn.status='cancelled';turn.text='Response stopped. Any already admitted workflow remains visible in Runs.'
        except (WorkflowError,SourceReadFailure,SourceFailure) as exc:
            turn.status='failed';turn.error_code=str(exc);turn.text='The request could not complete. Inspect the error and current case state before retrying.'
        except (ValidationError,TypeError,AttributeError):
            turn.status='failed';turn.error_code='CHAT_INVALID_OUTPUT';turn.text='Concierge returned an invalid structured response. No fallback answer was substituted.'
        except Exception:
            turn.status='failed';turn.error_code='CHAT_MODEL_OR_BACKEND_UNAVAILABLE';turn.text='The connected Concierge could not respond. No simulated answer was substituted.'
        finally:
            turn.telemetry.latency_ms=round((time.monotonic()-started)*1000)
            await run_in_threadpool(retain_turn,self.host,turn)

    def action(self,turn,operation,body,card):
        self.prune()
        if len(self.actions)>=256:raise WorkflowError('CHAT_BUSY')
        key='action_'+uuid4().hex
        self.actions[key]=PendingAction(turn.session_id,turn.actor_id,turn.context,operation,body,time.monotonic())
        card.action_id=key
        return card

    def filter_links(self,cards,actor):
        for card in cards:
            card.links=[l for l in card.links if not l.href.startswith("/control") or route_allowed(actor,l.href)]
            if not card.links:
                case=next((c for c in CASES if c in card.title),None)
                if case: card.links=[case_link(case)]
                else: card.links=[Link(label='Open program',href='/control/programs/PRG-A17')]

    async def dispatch(self,turn,route,scope,request,invoke):
        case=route.case_id or scope['case_id']
        selected=self.actor(request)
        capabilities=project(selected, selected=request.headers.get('x-stratos-demo-profile') is not None)
        permission=(capabilities.automation_save if route.intent=='AUTOMATION_CONFIGURATION' else
            bool(case and 'investigate' in capabilities.case_actions.get(case,[])) if route.intent=='INVESTIGATE' else
            bool(case and ('execute' if route.topic=='execute' else 'review') in capabilities.case_actions.get(case,[])) if route.intent=='ACT' else True)
        if not permission:
            turn.text='This demo identity cannot perform that action. You can inspect the case and its responsible role.'
            turn.cards=[Card(kind='status',title=case or 'Program status',links=[case_link(case)] if case else [Link(label='Overview',href='/control/overview')])]
            return
        if scope['case_id'] and case!=scope['case_id']:
            turn.text='This request names another case. Open that case before continuing; this draft remains in its original scope.'
            turn.cards=[Card(kind='navigation',title='Change case context',links=[case_link(case)])];return
        if route.intent in {'UNSUPPORTED','CLARIFY'}:
            turn.text='Please specify a supported case and whether you want its current status, an investigation, comparison, or governed decision. Concierge cannot change permissions or perform unsupported business actions.';return
        if route.intent=='AUTOMATION_CONFIGURATION':
            turn.classification='AUTOMATION_SAVE'
            if not case:turn.text='Choose a workflow/case for this configuration.';return
            if route.watch:
                if case!='QE-004':turn.text='Only the existing quality-exception watch is supported by this request.';return
                trigger=EventTrigger(system='manufacturing',event='quality_exception_created')
            elif route.cadence and route.time:
                trigger=ScheduleTrigger(cadence=route.cadence,time=route.time,timezone=route.timezone or 'America/Chicago',weekday=route.weekday)
            else:
                turn.text=('What time should the '+route.cadence+' check use (for example 7 AM CT)? '
                    if route.cadence and not route.time else
                    'Specify the cadence and time for the saved schedule (for example weekdays at 7 AM CT). ')
                turn.text+='This will be a saved configuration only; background execution stays disabled.'
                return
            config=AutomationInput(name=f'{case} '+('quality watch' if route.watch else 'readiness review'),workflow_id=CASES[case],case_scope=case,trigger=trigger,authority='read_only')
            card=Card(kind='automation',title='Save automation configuration',facts=[('Workflow',CASES[case].replace('_',' ')),('Scope','Helios · '+case),('Trigger',trigger_summary(trigger)),
                ('Authority','Read only'),('Background scheduler','Not enabled'),('Execution','Connected workflow · Saved configuration only')],required_role='automation or engineer',action_label='Save configuration',links=[Link(label='Open configurations',href='/control/workflows')])
            body=CreateAutomation(request_id='chat_save_'+turn.message_id[4:],configuration=config)
            turn.cards=[self.action(turn,'automation_save',body.model_dump(mode='json'),card)]
            turn.text='Review the configuration before saving. This does not activate a scheduler.';return
        if route.intent=='INVESTIGATE':
            turn.classification='RUN'
            if not case:turn.text='Choose the case to investigate.';return
            body=StartRequest(invocation_id='ui_chat_'+turn.message_id[4:],change_id=case,workflow_id='requirement_change_analysis' if case.startswith('CR') else CASES[case])
            # A model classification alone is not an instruction to start a workflow.
            explicit=bool(re.match(r'^(?:please\s+|can you\s+|could you\s+)?(?:reassess|investigate|run|process|route)\b',turn.user_text.strip(),re.I)) and not any(x in turn.user_text for x in ['"','```','“'])
            if not explicit:
                turn.text='Confirm the scoped investigation to start a real workflow run.'
                turn.cards=[self.action(turn,'investigate_'+case,body.model_dump(mode='json'),Card(kind='action',title='Investigate '+case,action_label='Start investigation',facts=[('Workflow',CASES[case]),('Scope','Helios · '+case)],links=[case_link(case)]))];return
            turn.telemetry.service_calls.append('WorkflowService.invoke')
            result=await invoke[case](body,request)
            turn.text='Workflow admitted. Follow the persisted run for its actual business outcome.'
            turn.cards=[Card(kind='run',title=case+' · '+words(result['status']),facts=[('Run',result['run_id']),('Invocation',body.invocation_id),('State','Admission is not a successful business outcome.')],run_id=result['run_id'],links=[Link(label='Open run',href='/control/runs/'+result['run_id']),case_link(case)])];return
        snapshot=business_snapshot(await run_in_threadpool(self.host.snapshot),selected)
        turn.telemetry.service_calls.append('ControlHost.snapshot (current source APIs)')
        if route.intent=='ACT':
            turn.classification='EXECUTION' if route.topic=='execute' else 'DECISION'
            if not case:turn.text='Open the exact case or decision before preparing an action.';return
            self.preview_decision(turn,snapshot,case,scope,route.topic)
            return
        if route.intent=='NAVIGATE':
            if not case:turn.text='Select a case to open its related record.';return
            links=[case_link(case)]
            if route.target=='workflow':links=[Link(label='Open workflow',href='/control/workflows/'+CASES[case])]
            elif route.target=='source':links=[source_link(case)]
            elif route.target=='evidence':links=[Link(label='Open evidence',href=CASE_ROOT+case+('?tab=evidence' if case=='CR-017' else '#evidence'))]
            elif route.target=='decision':links=[Link(label='Open decision',href=CASE_ROOT+case+'#decision' if case!='CR-017' else '/control/decisions')]
            elif route.target=='run':
                selected=next((r for r in all_runs(snapshot) if r.change_id==case and (not scope['run_id'] or scope['run_id']==r.run_id)),None)
                if not selected:turn.text='No persisted run is available for this scope.';return
                links=[Link(label='Open run',href='/control/runs/'+selected.run_id)]
            turn.text='Open the existing workbench to inspect the record.';turn.cards=[Card(kind='navigation',title=case,links=links)];return
        if route.intent=='EXPLAIN' and route.topic=='knowledge':
            from ..knowledge.concierge import explain_knowledge
            await explain_knowledge(self.host,turn,route,scope,selected_actor=self.actor(request),snapshot=snapshot,case=case)
            return
        if route.topic=='run' or scope['run_id']:
            runs=[r for r in all_runs(snapshot) if (not case or r.change_id==case) and (not scope['run_id'] or r.run_id==scope['run_id'])]
            turn.cards=[run_card(r) for r in sorted(runs,key=lambda r:(r.status=='running',r.started_at),reverse=True)[:8]]
            turn.text='Persisted workflow outcomes. Runtime completion is separate from review, execution and verification.' if runs else 'No workflow runs are recorded in this scope.';return
        selected=[case] if case else list(CASES)
        for current in selected:
            try:
                cards=await run_in_threadpool(grounded_cards,self.host,snapshot,current,'options' if route.intent=='COMPARE' else route.topic)
                if not case:
                    cards=[c for c in cards if c.kind=='status' and c.title.startswith(current)][:1]
                    names={'Current case state','Current source','Next step','Coverage satisfied','Engineering review','Touchless eligibility','Held quantity','Eligible quantity','Requested quantity','Gap quantity','Technical readiness'}
                    for card in cards:card.facts=[f for f in card.facts if f[0] in names]
                turn.cards.extend(cards)
            except SourceReadFailure:
                turn.cards.append(Card(kind='status',title=current+' · Current source unavailable',links=[case_link(current)]))
        if not case:
            # Do not sum QE/DR material: source references identify overlap explicitly.
            q=snapshot.quality.context if snapshot.quality and snapshot.quality.context else None
            d=snapshot.delivery.context if snapshot.delivery and snapshot.delivery.context else None
            shared=sorted({m.id for m in q.material}&{m.id for m in d.material}) if q and d else []
            turn.text='Current Helios cases, shown separately. '+('Shared material '+', '.join(shared)+' is counted once per case calculation; do not add the case gaps together.' if shared else 'No combined supply total is inferred.')
        else:
            turn.text='Current source-backed '+('options' if route.intent=='COMPARE' else 'state')+' for '+case+'.'
            if route.topic in {'policy','decision'}:
                why=next((value for card in turn.cards for key,value in card.facts if key=='Why approval is required'),None)
                if why:turn.text=why

    def preview_decision(self,turn,snapshot,case,scope,topic):
        v=views(snapshot)[case]
        if not v or not v.source_available:raise WorkflowError('SOURCE_READ_FAILED')
        if case=='CR-019':
            turn.text='CR-019 uses the bounded standard policy. Send “Process CR-019” to evaluate eligibility and invoke the existing handoff.'
            turn.cards=grounded_cards(self.host,snapshot,case,'policy');return
        if case=='CR-017':
            p=next((p for p in v.proposals if (not scope['proposal_id'] or (p.proposal.proposal_id==scope['proposal_id'] and p.proposal.proposal_version==scope['proposal_version'])) and (not scope['run_id'] or p.proposal.origin.run_id==scope['run_id']) and (scope['proposal_id'] or p.effective_status!='superseded')),None)
            if not p:turn.text='No exact proposal is recorded. Investigate the case first, then open the resulting decision.';turn.cards=[Card(kind='navigation',title=case,links=[case_link(case)])];return
            ref=p.execution.reference;plan=p.proposal.source_plan
            facts=[('Proposal',f'{ref.proposal_id} · v{ref.proposal_version}'),('Digest',ref.proposal_digest),('State',p.effective_status),
                *fields(plan,['configuration_id','procedure_id','sample_id','slot_id','cost_cents','currency','timing']),('Exact actions',words([a.model_dump(mode='json') for a in p.proposal.actions]))]
            card=Card(kind='decision',title='CR-017 · Exact validation proposal',facts=facts,required_role='Engineering Approver',links=[Link(label='Open decision',href=f'/control/decisions/{ref.proposal_id}/{ref.proposal_version}?digest={ref.proposal_digest}')])
            operation='cr017_execute' if topic=='execute' else 'cr017_review'
            body={'reference':ref.model_dump(mode='json')}
            if topic!='execute':body.update(decision='approve',comment='Explicit exact-proposal confirmation from Stratos Concierge.')
            allowed=p.current_check=='current' and p.effective_status in ({'approved'} if topic=='execute' else {'proposal_ready','waiting_for_approval'})
        else:
            progress=next((p for p in v.progress if not scope['run_id'] or p.run_id==scope['run_id']),None)
            plan=next((p for p in v.records.plans if progress and p.id==progress.plan_id),None) if v.records else None
            if not plan:turn.text='No exact source proposal is recorded. Investigate this case before requesting its governed decision.';turn.cards=[Card(kind='navigation',title=case,links=[case_link(case)])];return
            decision=next((d for d in v.records.decisions if d.plan_id==plan.id),None)
            body={'run_id':progress.run_id,'plan_id':plan.id,'plan_version':plan.plan_version,'plan_digest':plan.plan_digest}
            facts=[('Proposal',f'{plan.id} · v{plan.plan_version}'),('Digest',plan.plan_digest),('State',v.status),('Decision',decision.decision if decision else 'Pending'),
                *fields(plan,['quantity','committed_at','date_semantics','destination','permitted_actions'] if case=='DR-009' else ['permitted_action','recovery_owner']),
                ('Authority','Host-controlled execution. No material release or reallocation; acceptance and delivery remain separate.')]
            card=Card(kind='decision',title=case+' · Exact source proposal',facts=facts,required_role='Program Owner',links=[Link(label='Open decision',href=CASE_ROOT+case+'#decision')])
            operation=('delivery' if case=='DR-009' else 'quality')+('_execute' if topic=='execute' else '_review')
            if topic!='execute':body.update(decision='approve',comment='Explicit exact-proposal confirmation from Stratos Concierge.')
            allowed=v.status not in {'stale','verified'} and (bool(decision and decision.decision=='approve') if topic=='execute' else decision is None)
        turn.text='Concierge can prepare this request. Human approval and host-controlled execution require separate explicit confirmations.'
        if allowed:
            card.action_label='Execute approved plan' if topic=='execute' else 'Submit approval'
            self.action(turn,operation,body,card)
        else:turn.text='This proposal is not available for that action. Inspect its current review, freshness and execution state.'
        turn.cards=[card]

    async def confirm(self,session,action_id,body,request,actions,invoke):
        async with self.confirm_lock:
            pending=self.actions.get(action_id)
            selected=self.actor(request,True)
            self.session_access(session,selected)
            if pending and pending.actor_id!=selected.actor_id:raise WorkflowError('CHAT_SESSION_FORBIDDEN')
            if not pending or pending.session_id!=session or time.monotonic()-pending.created>1800:raise WorkflowError('CHAT_ACTION_EXPIRED')
            if pending.context!=body.context:raise WorkflowError('CHAT_CONTEXT_CHANGED')
            await run_in_threadpool(resolve,self.host,body.context)
            if pending.operation.startswith('investigate_'):
                case=pending.operation.removeprefix('investigate_')
                value=await invoke[case](StartRequest.model_validate(pending.body),request)
                await run_in_threadpool(retain_confirmation,self.host,session,pending.operation,self.actor(request).actor_id,value['status'],pending.body,value)
                return {'text':'Workflow admitted. Follow the run for its business outcome.','cards':[Card(kind='run',title=case+' · '+words(value['status']),run_id=value['run_id'],links=[Link(label='Open run',href='/control/runs/'+value['run_id'])])]}
            for turn in self.turns.values():
                if turn.session_id==session and any(c.action_id==action_id for c in turn.cards):
                    # Safe service hook; no payloads, credentials or model reasoning.
                    turn.telemetry.service_calls.append('Explicit confirmation: '+pending.operation)
                    turn.telemetry.service_calls=turn.telemetry.service_calls[-32:]
            schema,handler=actions[pending.operation]
            # Calls the SAME host endpoint handlers: role, scope, stale/exact-plan,
            # source authorization, durable idempotency and readback remain there.
            try:
                result=await run_in_threadpool(handler,schema.model_validate(pending.body),request)
            except WorkflowError as exc:
                await run_in_threadpool(retain_confirmation,self.host,session,pending.operation,self.actor(request).actor_id,str(exc),pending.body)
                raise
            await run_in_threadpool(retain_confirmation,self.host,session,pending.operation,self.actor(request).actor_id,getattr(result,'status','Recorded'),pending.body,result.model_dump(mode='json'))
            if pending.operation=='automation_save':
                return {'text':'Automation configuration saved. Background execution is not enabled in this demo.','cards':[Card(kind='automation',title=result.name,facts=[('State',result.configuration_state),('Background execution','Not enabled')],links=[Link(label='Open configuration',href='/control/automations/'+result.automation_id)])]}
            status=getattr(result,'status','Recorded')
            return {'text':'Host action returned: '+words(status)+'. Inspect current source readback and remaining work.','cards':[Card(kind='status',title='Governed action · '+words(status),facts=fields(result,['status','error_code']),links=[Link(label='Open decisions',href='/control/decisions')])]}


def attach(app,host,actor,actions,invoke):
    service=Concierge(host,manager=getattr(host,'concierge_manager',None))
    service.actor=actor
    if host is not None: host.concierge=service
    @app.post('/control-api/concierge/messages',response_model=Turn,status_code=202)
    async def send(body:ChatRequest,request:Request):
        actor(request).require_scope('CUST-FML01','PRG-A17')
        return await service.start(body,request,invoke)
    @app.get('/control-api/concierge/{session}/{message}',response_model=Turn)
    def read(session:str,message:str,request:Request):
        actor(request).require_scope('CUST-FML01','PRG-A17')
        service.session_access(session,actor(request))
        return service.visible_turn(service.get(session,message),actor(request))
    @app.post('/control-api/concierge/{session}/{message}/cancel',response_model=Turn)
    async def cancel(session:str,message:str,body:Confirmation,request:Request):
        actor(request,True).require_scope('CUST-FML01','PRG-A17')
        service.session_access(session,actor(request))
        turn=service.get(session,message)
        if body.context!=turn.context:raise WorkflowError('CHAT_CONTEXT_CHANGED')
        task=service.tasks.get((session,message))
        if task:
            task.cancel();await asyncio.gather(task,return_exceptions=True)
            if turn.status=='running':
                turn.status='cancelled';turn.text='Response stopped before processing.'
        await run_in_threadpool(retain_turn,host,turn)
        return turn
    @app.post('/control-api/concierge/{session}/actions/{action_id}')
    async def confirm(session:str,action_id:str,body:Confirmation,request:Request):
        actor(request,True).require_scope('CUST-FML01','PRG-A17')
        result=await service.confirm(session,action_id,body,request,actions,invoke)
        service.filter_links(result['cards'],actor(request))
        return result
    @app.get('/control-api/concierge-runs/{run_id}',response_model=Card)
    def progress(run_id:str,request:Request):
        actor(request).require_scope('CUST-FML01','PRG-A17')
        # Metadata read only; no model calls and no expensive source snapshot polling.
        with host.store.transaction() as data:
            run=data.runs.get(run_id);case=data.cases.get(run.case_id) if run else None
            if not case or (case.customer_id,case.program_id)!=('CUST-FML01','PRG-A17') or case.change_id not in CASES:raise WorkflowError('RUN_NOT_FOUND')
            outcome='Investigation in progress' if run.status=='running' else 'Investigation failed' if run.status!='completed' else 'Analysis completed · Inspect current case for business outcome'
            if run.recommendation and run.recommendation.policy_path=='escalation_required':outcome='Escalation required'
            p=data.standard_handoffs.get(run_id) or data.quality_recoveries.get(run_id) or data.delivery_commitments.get(run_id)
            if p:outcome=words(p.status)
            view=host.run_view(run,change_id=case.change_id);view.business_outcome=outcome
            card=run_card(view)
            card.links=[l for l in card.links if not l.href.startswith('/control') or route_allowed(actor(request),l.href)]
            return card
