"""Local, single-host CR-017 adapter. Existing services retain all business authority."""
import asyncio
from contextlib import asynccontextmanager
import fcntl
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ..models import CaseState, ProgramChangeEvent
from ..application.models import WorkflowInvocation, WorkflowError, now_utc, Trigger
from ..application.demo_identity import READER, AUTOMATION, ENGINEER, PROGRAM_OWNER
from ..application.service import WorkflowService
from ..application.execution import ExecutionService, reference, proposal_key
from ..application.execution_models import SourceFailure, SourceReadFailure, HumanReview, ExecutionRecord, ProposalRef, OperatorEscalation
from ..application.contracts import digest
from . import downstream, standard_change, quality, delivery
from ..application.delivery_commitment import DeliveryCommitmentService
from ..application.delivery_models import DeliveryActionRequest, DeliveryReviewRequest, DeliveryProgress, DeliveryReconcileRequest
from .models import DeliveryCaseView
from ..application.quality_recovery import QualityRecoveryService
from ..application.quality_recovery_models import QualityActionRequest, QualityReviewRequest, QualitySubmissionRequest, QualityProgress, QualityReconcileRequest
from .quality import QualityCaseView
from ..application.standard_handoff import StandardHandoffService
from ..application.standard_handoff_models import HandoffActionRequest, StandardHandoff
from .models import StandardCaseView
from .workflows import RunDetail, business_outcome
from ..application.workflow_catalog import workflow_catalog, get_workflow, CatalogWorkflow
from ..application.automations import (AutomationStore, AutomationView, CreateAutomation, UpdateAutomation,
    ChangeConfigurationState, DeleteAutomation, DeletedAutomation)
from .models import StartRequest, StartResponse, PrepareRequest, EscalationRequest, EvidenceEscalationRequest, ExactRequest, ReviewRequest, CaseView, RunView, SpecialistView, ProposalView

from .access import (ACTORS, Capabilities, resolve_actor, project, require_action, require_surface, business_snapshot, business_case, decision_queue)
from .integration_models import DecisionSummary
SCOPE = ('CUST-FML01', 'PRG-A17')
STALE_CODES = {'STALE_SOURCE', 'STALE_EVIDENCE', 'STALE_PLAN', 'STALE_MILESTONE', 'PROPOSAL_NOT_CURRENT', 'APPROVAL_POLICY_MISMATCH'}

class ControlHost:
    def __init__(self, store, source, human, config, investigate, event, *, mode='live_model', demo_settings=None, max_concurrent_workflow_runs=None):
        self.store, self.source, self.human = store, source, human
        self.execution = ExecutionService(store, source)
        self.automations = AutomationStore(store.directory)
        self.standard = StandardHandoffService(store, source)
        self.quality = QualityRecoveryService(store, source, human)
        self.delivery = DeliveryCommitmentService(store, source, human)
        self.config, self.event, self.mode = config, event, mode
        self.artifacts = store.directory / 'runs'
        self.admission = asyncio.Lock()
        self.tasks = set()
        self.run_tasks = {}
        import os
        self.max_concurrent_workflow_runs = int(max_concurrent_workflow_runs if max_concurrent_workflow_runs is not None else os.environ.get('STRATOS_MAX_CONCURRENT_WORKFLOW_RUNS', '3'))
        if not 1 <= self.max_concurrent_workflow_runs <= 8:
            raise ValueError('STRATOS_MAX_CONCURRENT_WORKFLOW_RUNS must be between 1 and 8')
        self.investigate = investigate
        if demo_settings is not None:
            from .demo_management import DemoManagement
            self.demo_management = DemoManagement(self, demo_settings)

    def checkpoint_path(self, run):
        # Never use a browser or metadata-supplied filesystem path.
        return self.artifacts / run.run_id / 'case-state.json'

    def runtime_mode(self, change_id):
        # Owned by the installed runtime, never a browser-supplied mode switch.
        return getattr(self.investigate, 'case_modes', {}).get(change_id, self.mode)

    def run_view(self, run, *, change_id="CR-017"):
        raw = run.model_dump(mode='json')
        view = RunView(**{k: raw[k] for k in RunView.model_fields if k in raw}, findings_state='not_recorded', change_id=change_id)
        path = self.checkpoint_path(run)
        if path.is_file():
            try:
                if path.is_symlink() or path.parent.is_symlink() or path.stat().st_size > 4_000_000:
                    raise ValueError('unsafe checkpoint')
                state = CaseState.model_validate_json(path.read_text())
                if (state.run_id, state.case_id, state.customer_id, state.program_id, state.event.change_id) != (run.run_id, run.case_id, *SCOPE, change_id):
                    raise ValueError('checkpoint scope mismatch')
                results = {a.invocation_id: a.assessment for a in state.completed_assessments}
                view.specialists = [SpecialistView(invocation_id=i.invocation_id,
                    parent_invocation_id=i.parent_invocation_id, caller=i.caller, specialist=i.specialist,
                    status=i.status, task=i.question, result_kind=i.result_kind, depth=i.depth,
                    started_ms=i.started_ms, ended_ms=i.ended_ms,
                    summary=results[i.invocation_id].summary if i.invocation_id in results else None,
                    source_references=[r for r in results[i.invocation_id].source_references if r.tool_name!='verify_knowledge_document'] if i.invocation_id in results else [],
                    unresolved_questions=results[i.invocation_id].unresolved_questions if i.invocation_id in results else [],
                    error_code='SPECIALIST_FAILED' if i.error else None) for i in state.requested_specialists]
                view.findings_state = 'recorded'
            except (ValueError, OSError):
                view.findings_state = 'unavailable'
        return view

    def snapshot(self):
        with self.store.transaction() as data:
            cases = [c for c in data.cases.values() if (c.customer_id, c.program_id, c.change_id) == (*SCOPE, 'CR-017')]
            ids = {c.case_id for c in cases}
            runs = sorted([r for r in data.runs.values() if r.case_id in ids and (r.customer_id, r.program_id) == SCOPE], key=lambda r: r.started_at, reverse=True)
            proposals = [p for p in data.proposals.values() if p.origin.case_id in ids and proposal_key(reference(p)) in data.executions]
            activity = [e for e in data.activity if e.case_id in ids and (e.customer_id, e.program_id) == SCOPE]
        available = True
        change = None
        coverage = None
        try:
            change = self.source.read.get_change_request('CR-017')
            coverage = self.source.read.get_validation_coverage('CR-017')
        except SourceReadFailure:
            available = False
        physical = None
        if available:
            try:
                physical = downstream.view(self)
            except SourceReadFailure:
                available = False
        projected = []
        for p in sorted(proposals, key=lambda p: str(p.created_at), reverse=True):
            ref = reference(p)
            inspected = self.execution.inspect(ref)
            record = data.executions[proposal_key(ref)]
            check, effective = 'current', record.status
            if record.status in {'stale', 'superseded', 'rejected'}:
                check = record.status
            elif record.status == 'completed_execution' and physical and physical.physical.completion and physical.physical.completion.plan_id == p.source_plan.id:
                check = 'completed_before_lab_result'
            elif available:
                try:
                    self.execution._current(p, record)  # Read-only existing Phase 06 freshness preflight; writes recheck.
                except SourceReadFailure:
                    check, available = 'SOURCE_READ_FAILED', False
                except WorkflowError as exc:
                    check = str(exc)
                    if check in STALE_CODES:
                        effective = 'stale'
            else:
                check = 'SOURCE_READ_FAILED'
            replacement = next((reference(q) for q in proposals if q.proposal_id != p.proposal_id and q.origin.case_id == p.origin.case_id
                and data.proposal_status.get(proposal_key(reference(q))) == 'current'), None) if effective == 'superseded' else None
            projected.append(ProposalView(**{k: v for k, v in inspected.items() if k != 'activity'}, current_check=check,
                effective_status=effective, replacement=replacement))
        views = [self.run_view(r) for r in runs]
        standard = standard_change.snapshot(self)
        quality_view = quality.snapshot(self)
        autonomous_view = quality.snapshot(self, 'QE-011')
        delivery_view = delivery.snapshot(self)
        catalog = workflow_catalog()
        for view in views:
            view.business_outcome = business_outcome(view, projected, physical, available)
        for item in catalog:
            item.latest_run_id = next((r.run_id for r in (standard.runs if standard else []) if r.change_id == "CR-019"), None) if item.workflow_id == "standard_change" else next((r.run_id for r in sorted([*views,*getattr(standard,"runs",[])],key=lambda r:r.started_at,reverse=True) if r.workflow_id == item.workflow_id), None)
        for item in catalog:
            if item.workflow_id == "yield_exception_recovery":
                latest = sorted([*getattr(quality_view,'runs',[]),*getattr(autonomous_view,'runs',[])],key=lambda r:r.started_at,reverse=True)
                item.latest_run_id = latest[0].run_id if latest else None
        for item in catalog:
            if item.workflow_id == "delivery_readiness":
                item.latest_run_id = delivery_view.runs[0].run_id if delivery_view and delivery_view.runs else None
        escalations = sorted([e for e in data.operator_escalations.values() if e.case_id in ids], key=lambda e:e.submitted_at, reverse=True)
        result = CaseView(case_runtime_modes={c:self.runtime_mode(c) for c in ('CR-017','CR-019','QE-004','DR-009','QE-011')}, delivery=delivery_view, quality=quality_view, autonomous_quality=autonomous_view, standard=standard, workflows=catalog, automations=self.automations.list(READER), mode=self.mode, source_url=self.source.config.base_url, fetched_at=now_utc(), source_available=available, cases=cases,
            runs=views, proposals=projected, operator_escalations=escalations, activity=activity[-200:], downstream=physical)
        opening = getattr(self, 'autonomous', None)
        result.pending_source_event = bool(opening and opening.state().status in {'armed','event_emitted'} and opening.timer and not opening.timer.done())
        from .integration import summarize
        result.case_summaries, result.decision_summaries, result.dependencies = summarize(result,change,coverage)
        return result

    def prepare(self, request):
        with self.store.transaction() as data:
            run = data.runs.get(request.run_id)
            if run and data.cases[run.case_id].change_id != 'CR-017':
                raise WorkflowError('STANDARD_INTAKE_ONLY')
            if run and (run.trigger.source_reference or '').startswith('evidence_'):
                raise WorkflowError('DOWNSTREAM_READ_ONLY')
            if run and not any(e.run_id == run.run_id for e in data.operator_escalations.values()):
                raise WorkflowError('OPERATOR_ESCALATION_REQUIRED')
        # A stable host-generated preparation key recovers lost responses without new plans.
        key = 'ui_prepare_' + digest(request.model_dump(mode='json'))[:40]
        return self.execution.prepare(request.run_id, key, supersedes=request.supersedes)

    def escalate(self, request, actor):
        value = None
        requires_proposal = False
        with self.store.transaction(write=True) as data:
            run = data.runs.get(request.run_id)
            if not run: raise WorkflowError('RUN_NOT_FOUND')
            case = data.cases.get(run.case_id)
            if not case or case.change_id != 'CR-017': raise WorkflowError('CASE_SCOPE_MISMATCH')
            if run.status != 'completed' or not run.recommendation: raise WorkflowError('RECOMMENDATION_NOT_READY')
            if run.recommendation.policy_path not in {'escalation_required','human_review_required'}:
                raise WorkflowError('ESCALATION_NOT_REQUIRED')
            actor.require_scope(run.customer_id, run.program_id)
            rec_digest = digest(run.recommendation.model_dump(mode='json'))
            value = OperatorEscalation(escalation_id=request.submission_id,run_id=run.run_id,case_id=run.case_id,
                customer_id=run.customer_id,program_id=run.program_id,subject=request.subject.strip(),
                recommendation=request.recommendation.strip(),business_context=request.business_context.strip(),
                operator_notes=request.operator_notes.strip(),recommendation_digest=rec_digest,
                submitted_by=actor.actor_id,submitted_at=now_utc())
            old=data.operator_escalations.get(value.escalation_id)
            if old:
                same=(old.run_id==value.run_id and old.subject==value.subject and
                    old.recommendation==value.recommendation and old.business_context==value.business_context and
                    old.operator_notes==value.operator_notes and old.recommendation_digest==value.recommendation_digest)
                if not same: raise WorkflowError('ESCALATION_ID_CONFLICT')
                value = old
            if any(e.run_id==run.run_id for e in data.operator_escalations.values()):
                value = next(e for e in data.operator_escalations.values() if e.run_id==run.run_id)
            else:
                data.operator_escalations[value.escalation_id]=value
            requires_proposal = run.recommendation.policy_path == 'human_review_required'

        # Submitting the operator-authored handoff is the sole UI boundary that
        # places a supported CR-017 proposal into Engineering's review queue.
        if requires_proposal:
            with self.store.transaction() as data:
                existing = next((p for p in data.proposals.values() if p.origin.run_id == request.run_id), None)
                active = next((p for key, p in data.proposals.items()
                    if p.origin.case_id == run.case_id and key in data.executions
                    and data.executions[key].status != 'superseded'), None)
            if existing is None:
                self.execution.prepare(request.run_id, 'operator_escalation_' + value.escalation_id,
                    supersedes=reference(active) if active else None)
        return value

    def escalate_evidence(self, request, actor):
        current = downstream.view(self)
        if (not current.review_ready or current.physical.evidence_digest != request.expected_evidence_digest
                or not current.assessment or current.assessment.run_id != request.run_id):
            raise WorkflowError('EVIDENCE_REASSESSMENT_REQUIRED')
        with self.store.transaction(write=True) as data:
            run = data.runs.get(request.run_id)
            if (not run or run.status != 'completed' or not run.recommendation
                    or run.trigger.source_reference != 'evidence_' + request.expected_evidence_digest):
                raise WorkflowError('RECOMMENDATION_NOT_READY')
            actor.require_scope(run.customer_id, run.program_id)
            value = OperatorEscalation(escalation_id=request.submission_id, run_id=run.run_id,
                case_id=run.case_id, customer_id=run.customer_id, program_id=run.program_id,
                stage='evidence_review', evidence_digest=request.expected_evidence_digest,
                subject=request.subject.strip(), recommendation=request.recommendation.strip(),
                business_context=request.business_context.strip(), operator_notes=request.operator_notes.strip(),
                recommendation_digest=digest(run.recommendation.model_dump(mode='json')),
                submitted_by=actor.actor_id, submitted_at=now_utc())
            old = data.operator_escalations.get(value.escalation_id)
            if old:
                if old.model_dump(mode='json', exclude={'submitted_at'}) != value.model_dump(mode='json', exclude={'submitted_at'}):
                    raise WorkflowError('ESCALATION_ID_CONFLICT')
                return old
            prior = next((e for e in data.operator_escalations.values()
                if e.stage == 'evidence_review' and e.evidence_digest == request.expected_evidence_digest), None)
            if prior:
                return prior
            data.operator_escalations[value.escalation_id] = value
            return value

    async def start(self, request, actor, *, event=None, evidence_digest=None, trigger=None, expected_quality_digest=None):
        require_action(actor, request.change_id, "investigate")
        if (request.change_id in {'QE-004','QE-011'}) != (request.workflow_id == 'yield_exception_recovery'):
            raise WorkflowError('CASE_SCOPE_MISMATCH')
        if (request.change_id == 'DR-009') != (request.workflow_id == 'delivery_readiness'):
            raise WorkflowError('CASE_SCOPE_MISMATCH')
        if request.change_id == 'DR-009':
            event = delivery.event(await run_in_threadpool(self.delivery.context))
        if request.change_id in {'QE-004','QE-011'}:
            context = await run_in_threadpool(self.quality.context, request.change_id)
            if expected_quality_digest is not None and context.context_digest != expected_quality_digest:
                raise WorkflowError('STALE_SOURCE_EVENT')
            event = quality.event(context)
        if request.change_id == 'CR-019':
            event = standard_change.event(await run_in_threadpool(self.standard.context))
        if event is not None and event.change_id != request.change_id:
            raise WorkflowError('CASE_SCOPE_MISMATCH')
        incoming = WorkflowInvocation(invocation_id=request.invocation_id, workflow_id=request.workflow_id,
            definition_version=request.definition_version, operation=request.operation, customer_id=request.customer_id,
            program_id=request.program_id, event=event or self.event,
            trigger=trigger or Trigger(source_reference=('evidence_' + evidence_digest) if evidence_digest else None))
        started = asyncio.Event()
        async def investigate(incoming, run):
            from .concurrency import settled_thread
            started.set()  # WorkflowService has durably claimed the invocation before this point.
            from ..knowledge.integration import KnowledgeContext, current_knowledge_context
            token = current_knowledge_context.set(KnowledgeContext(self.knowledge, actor))
            try:
                state = await self.investigate(incoming, run, self.checkpoint_path(run))
            finally:
                current_knowledge_context.reset(token)
            if incoming.event.change_id == 'DR-009':
                await settled_thread(self.delivery.process, run, state)
            if incoming.event.change_id in {'QE-004','QE-011'}:
                await settled_thread(self.quality.process, run, state)
            if incoming.event.change_id == 'CR-019':
                await settled_thread(self.standard.process, run, state)
            if evidence_digest:
                await settled_thread(downstream.record_assessment, self, run, state, evidence_digest)
            return state
        service = WorkflowService(self.store, config=self.config, investigate=investigate, actors=list(ACTORS.values()), execution_mode=self.runtime_mode(request.change_id))
        async with self.admission:
            with self.store.transaction() as data:
                replay = next((r for r in data.runs.values() if r.invocation_id == incoming.invocation_id), None)
                active = [r for r in data.runs.values() if r.status == 'running' or r.run_id in self.run_tasks]
                same_case = any((r.customer_id,r.program_id,data.cases[r.case_id].change_id) ==
                    (incoming.event.customer_id,incoming.event.program_id,incoming.event.change_id) for r in active)
            if replay:
                result = await service.invoke(incoming, actor)
                if result.error_code:
                    raise WorkflowError(result.error_code)
                return {'run_id': result.run.run_id, 'status': result.status, 'replayed': True}
            if same_case:
                raise WorkflowError('RUN_ALREADY_RUNNING')
            if max(len(active), len(self.tasks)) >= self.max_concurrent_workflow_runs:
                raise WorkflowError('WORKFLOW_CAPACITY_REACHED')
            async def run():
                result = await service.invoke(incoming, actor)
                if incoming.event.change_id == 'CR-017' and not evidence_digest and result.status == 'completed' and result.run.recommendation.policy_path == 'human_review_required':
                    try:
                        from .concurrency import settled_thread
                        await settled_thread(self.prepare, PrepareRequest(run_id=result.run.run_id))
                    except Exception as exc:
                        with self.store.transaction(write=True) as data:
                            self.store._activity(data, result.run, 'execution_denied', actor=AUTOMATION,
                                details={'error_code': str(exc) if isinstance(exc, WorkflowError) else 'HOST_PREPARATION_FAILED', 'operation': 'prepare_proposal'})
                return result
            task = asyncio.create_task(run())
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
            signal = asyncio.create_task(started.wait())
            await asyncio.wait([task, signal], return_when=asyncio.FIRST_COMPLETED)
            signal.cancel()
            await asyncio.gather(signal, return_exceptions=True)
            if task.done():
                result = task.result()
                if result.error_code and not result.run:
                    raise WorkflowError(result.error_code)
            with self.store.transaction() as data:
                claimed = next(r for r in data.runs.values() if r.invocation_id == incoming.invocation_id)
            self.run_tasks[claimed.run_id] = task
            task.add_done_callback(lambda _: self.run_tasks.pop(claimed.run_id, None))
            return {'run_id': claimed.run_id, 'status': claimed.status, 'replayed': False}


def create_app(host, *, allowed_origins=('http://127.0.0.1:5188',), allowed_hosts=('127.0.0.1',)):
    @asynccontextmanager
    async def lifespan(app):
        host.store.directory.mkdir(parents=True, exist_ok=True)
        # One HTTP host owns admission for this dedicated metadata directory.
        with (host.store.directory / 'control-host.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('CONTROL_HOST_ALREADY_RUNNING') from None
            host.automations.seed_examples()
            if getattr(host, 'autonomous', None):
                host.autonomous.startup()
            # Recovery is explicit and truthful. Host startup never resumes or
            # creates work; demo app entry or explicit replay arms the source event.
            with host.store.transaction() as data:
                abandoned = [r.run_id for r in data.runs.values() if r.status == 'running' and r.invocation_id.startswith('ui_')]
            for run_id in abandoned:
                host.store.finish(run_id, error_code='HOST_INTERRUPTED')
            yield
            if getattr(host, 'autonomous', None):
                await host.autonomous.stop()
            pending = list(host.tasks) + list(host.concierge.tasks.values())
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)

    app = FastAPI(title='Stratos workflow control host', lifespan=lifespan, docs_url=None, redoc_url=None)
    app.state.control_host = host
    from .knowledge import install as install_knowledge
    install_knowledge(app, host)

    def failure(code, status=409):
        return JSONResponse({'error': {'code': code}}, status_code=status, headers={'Cache-Control': 'no-store'})

    @app.middleware('http')
    async def boundary(request, call_next):
        if request.url.hostname not in allowed_hosts or request.headers.get('sec-fetch-site') == 'cross-site':
            return failure('LOCAL_ORIGIN_REQUIRED', 403)
        if request.method not in {'GET', 'HEAD'}:
            if request.headers.get('x-stratos-action') != '1' or request.headers.get('origin') not in allowed_origins:
                return failure('LOCAL_ORIGIN_REQUIRED', 403)
        try:
            management = getattr(host, 'demo_management', None)
            if management:
                async with management.request_lease(
                    reset=request.url.path in {'/control-api/demo/reset','/control-api/demo/autonomous/prepare','/control-api/demo/autonomous/reset'},
                    wait_reset=request.url.path == '/control-api/demo/autonomous/enter',
                ):
                    state = management.state()
                    if request.method not in {'GET','HEAD'} and not request.url.path.startswith('/control-api/demo/'):
                        if state.recovery_required:
                            return failure('DEMO_RESET_RECONCILIATION_REQUIRED', 409)
                        epoch = request.headers.get('x-stratos-demo-epoch')
                        if epoch is not None and epoch != state.epoch:
                            return failure('DEMO_STATE_CHANGED', 409)
                    response = await call_next(request)
                    response.headers['X-Stratos-Demo-Epoch'] = management.state().epoch
            else:
                response = await call_next(request)
        except WorkflowError as exc:
            return failure(str(exc), 409)
        except Exception:
            return failure('HOST_UNAVAILABLE', 503)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return failure('INVALID_CONTROL_REQUEST', 422)

    @app.exception_handler(WorkflowError)
    async def denied(request, exc):
        import logging
        logging.getLogger("stratos.access").warning("Host request denied: %s", str(exc))
        return failure(str(exc), 403 if str(exc) in {'WRONG_APPROVER', 'DEMO_IDENTITY_REQUIRED', 'DEMO_PROFILE_FORBIDDEN', 'EXECUTION_ROLE_FORBIDDEN', 'SCOPE_FORBIDDEN', 'SURFACE_FORBIDDEN', 'CHAT_SESSION_FORBIDDEN'} else 404 if str(exc) in {'AUTOMATION_NOT_FOUND', 'RUN_NOT_FOUND', 'UNKNOWN_WORKFLOW'} else 409)

    @app.exception_handler(SourceReadFailure)
    @app.exception_handler(SourceFailure)
    async def source_failure(request, exc):
        return failure(str(exc), 503)

    actor = resolve_actor
    from .agent_workspace import attach as attach_agent_workspace
    attach_agent_workspace(app,host,actor)

    @app.get("/control-api/capabilities", response_model=Capabilities)
    def capabilities(request: Request, customer_id: str = SCOPE[0], program_id: str = SCOPE[1]):
        if (customer_id, program_id) != SCOPE: raise WorkflowError("SCOPE_FORBIDDEN")
        return project(actor(request), selected=request.headers.get("x-stratos-demo-profile") is not None)

    @app.get("/control-api/decisions", response_model=list[DecisionSummary])
    def decisions(request: Request):
        selected = actor(request)
        require_surface(selected, "decisions")
        return decision_queue(host.snapshot(), selected)

    @app.get('/control-api/health')
    def health():
        return {'status': 'ok', 'mode': host.mode, 'scope': 'CR-017', 'demo_identity': True}

    @app.get('/control-api/readiness')
    def readiness(request: Request):
        actor(request).require_scope(*SCOPE)
        from .readiness import observe
        return observe(host)

    @app.get('/control-api/cases/CR-017', response_model=CaseView)
    def case(request: Request):
        actor(request).require_scope(*SCOPE)
        return business_snapshot(host.snapshot(), actor(request))

    @app.post('/control-api/cases/CR-017/investigations', status_code=202, response_model=StartResponse)
    async def start(body: StartRequest, request: Request):
        selected = actor(request, True)
        if selected is READER:
            raise WorkflowError("EXECUTION_ROLE_FORBIDDEN")
        if body.change_id != 'CR-017':
            raise WorkflowError('CASE_SCOPE_MISMATCH')
        return await host.start(body, selected)

    @app.post('/control-api/proposals/prepare', response_model=ProposalRef)
    def prepare(body: PrepareRequest, request: Request):
        require_action(actor(request, True), 'CR-017', 'prepare')
        return reference(host.prepare(body))

    @app.post('/control-api/cases/CR-017/escalations', response_model=OperatorEscalation)
    def submit_escalation(body: EscalationRequest, request: Request):
        selected=actor(request, True)
        require_action(selected, 'CR-017', 'escalate')
        return host.escalate(body, selected)

    @app.post('/control-api/proposals/review', response_model=HumanReview)
    def review(body: ReviewRequest, request: Request):
        require_action(actor(request, True), 'CR-017', 'review')
        with host.store.transaction() as data:
            if not any(e.run_id == body.reference.run_id for e in data.operator_escalations.values()):
                raise WorkflowError('OPERATOR_ESCALATION_REQUIRED')
        return host.execution.review(body.reference, body.decision, body.comment, actor(request, True), host.human)

    @app.post('/control-api/proposals/execute', response_model=ExecutionRecord)
    def execute(body: ExactRequest, request: Request):
        require_action(actor(request, True), 'CR-017', 'execute')
        # Authorized operator asks the existing automation host to resume the exact approved manifest.
        # No operation, target, arguments, source role or idempotency keys are accepted here.
        return host.execution.resume(body.reference, AUTOMATION)

    @app.post('/control-api/cases/CR-017/assess-validation-result', response_model=StartResponse, status_code=202)
    async def assess(body: downstream.AssessRequest, request: Request):
        selected = actor(request, True)
        require_action(selected, 'CR-017', 'reassess')
        physical = await run_in_threadpool(downstream.read_physical, host.source)
        if not physical.result or physical.evidence_digest != body.expected_evidence_digest:
            raise WorkflowError('CURRENT_RESULT_REQUIRED')
        with host.store.transaction() as data:
            if not any(e.status == 'completed_execution' and data.proposals[k].source_plan.id == physical.job.plan_id
                       for k, e in data.executions.items() if k in data.proposals):
                raise WorkflowError('VERIFIED_EXECUTION_REQUIRED')
            if body.retry_run_id:
                prior=data.runs.get(body.retry_run_id)
                expected='evidence_'+body.expected_evidence_digest
                if (not prior or (prior.customer_id,prior.program_id)!=SCOPE
                    or prior.workflow_id!='requirement_change_analysis'
                    or data.cases[prior.case_id].change_id!='CR-017'
                    or prior.trigger.source_reference!=expected or prior.status not in {'completed','failed'}
                    or any(a.run_id==prior.run_id and a.details.get('operation')=='assess_validation_result'
                           and a.details.get('confirmed') for a in data.activity)):
                    raise WorkflowError('REASSESSMENT_RETRY_NOT_ALLOWED')
        event = host.event.model_copy(update=dict(event_id='lab_result_' + body.expected_evidence_digest[:32],
            source_system='validation', received_at=physical.completion.completed_at,
            request_summary='Inspect CR-017 validation evidence after the recorded synthetic lab completion. Determine only whether current recorded evidence addresses the exact approved workload, configuration, versions, duration and unchanged criteria, using the Validation and Evidence specialist. This is a read-only evidence reassessment, not a request to establish end-to-end program completion. Preserve actual applicability mismatches and missing inputs needed to determine evidence adequacy as blockers. Report pending engineering disposition, customer acceptance, Planner tracking and unassigned follow-up ownership separately as known remaining stages or risks; they are not gaps in the validation evidence or unanswered inputs to this narrow adequacy question. Do not create new scheduling, approval, acceptance or ownership assignments.',
            # Intake establishes the existing job/plan. The Validation specialist
            # discovers the newly arrived result through scoped source reads;
            # the host independently binds its conclusion to the evidence digest.
            linked_record_ids=[physical.job.id, physical.job.plan_id],
            correlation_id='lab_result_' + body.expected_evidence_digest[:32]))
        invocation=('ui_evidence_retry_'+digest(body.model_dump(mode='json')) if body.retry_run_id
                    else 'ui_evidence_'+body.expected_evidence_digest)
        return await host.start(StartRequest(invocation_id=invocation), selected,
            event=event, evidence_digest=body.expected_evidence_digest)

    @app.post('/control-api/cases/CR-017/evidence-review', response_model=downstream.EvidenceReview)
    def evidence_review(body: downstream.ReviewEvidenceRequest, request: Request):
        require_action(actor(request, True), 'CR-017', 'review_evidence')
        with host.store.transaction() as data:
            if not any(e.stage == 'evidence_review' and e.evidence_digest == body.expected_evidence_digest
                       for e in data.operator_escalations.values()):
                raise WorkflowError('OPERATOR_ESCALATION_REQUIRED')
        return downstream.review_evidence(host, body, actor(request, True))

    @app.post('/control-api/cases/CR-017/evidence-escalations', response_model=OperatorEscalation)
    def submit_evidence_escalation(body: EvidenceEscalationRequest, request: Request):
        selected = actor(request, True)
        require_action(selected, 'CR-017', 'escalate')
        return host.escalate_evidence(body, selected)

    @app.get('/control-api/workflows', response_model=list[CatalogWorkflow])
    def workflows(request: Request):
        require_surface(actor(request), 'workflows')
        return host.snapshot().workflows

    @app.get('/control-api/workflows/{workflow_id}', response_model=CatalogWorkflow)
    def workflow(workflow_id: str, request: Request):
        item = next((w for w in workflows(request) if w.workflow_id == workflow_id), None)
        if not item:
            raise WorkflowError('UNKNOWN_WORKFLOW')
        return item

    @app.post('/control-api/workflows/{workflow_id}/runs', response_model=StartResponse, status_code=202)
    async def start_workflow(workflow_id: str, body: StartRequest, request: Request):
        selected = actor(request, True)
        if selected not in (AUTOMATION, ENGINEER):
            raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        item = get_workflow(workflow_id)
        if not item or not item.manual_available or item.invocation_workflow_id != body.workflow_id or body.change_id not in item.cases:
            raise WorkflowError('WORKFLOW_NOT_CONNECTED')
        # Identical invocation body/service to the existing case route, including replay across routes.
        return await host.start(body, selected)

    @app.get('/control-api/runs', response_model=list[RunView])
    def runs(request: Request):
        require_surface(actor(request), 'operations')
        snapshot = business_snapshot(host.snapshot(), actor(request))
        return snapshot.runs + (snapshot.standard.runs if snapshot.standard else []) + (snapshot.quality.runs if snapshot.quality else []) + (snapshot.delivery.runs if snapshot.delivery else []) + (snapshot.autonomous_quality.runs if snapshot.autonomous_quality else [])

    @app.get('/control-api/runs/{run_id}', response_model=RunDetail)
    def run_detail(run_id: str, request: Request):
        require_surface(actor(request), 'operations')
        snapshot = business_snapshot(host.snapshot(), actor(request))
        run = next((r for r in snapshot.runs + (snapshot.standard.runs if snapshot.standard else []) + (snapshot.quality.runs if snapshot.quality else []) + (snapshot.delivery.runs if snapshot.delivery else []) + (snapshot.autonomous_quality.runs if snapshot.autonomous_quality else []) if r.run_id == run_id), None)
        if not run:
            raise WorkflowError('RUN_NOT_FOUND')
        with host.store.transaction() as data:
            activity = [a for a in data.activity if a.run_id == run.run_id and a.case_id == run.case_id and (a.customer_id, a.program_id) == SCOPE]
        if run.change_id == 'DR-009':
            return RunDetail(run=run, business_question=snapshot.delivery.context.request.summary if snapshot.delivery.context else 'Delivery readiness',
                activity=activity, proposals=[], downstream=None, source_available=snapshot.delivery.source_available)
        if run.change_id in {'QE-004','QE-011'}:
            current = snapshot.quality if run.change_id == 'QE-004' else snapshot.autonomous_quality
            return RunDetail(run=run, business_question=current.context.exception.summary if current.context else 'Quality recovery',
                activity=activity, proposals=[], downstream=None, source_available=current.source_available)
        if run.change_id == 'CR-019':
            current = snapshot.standard
            return RunDetail(run=run, business_question=current.context.request.summary if current.context else 'Standard validation package',
                activity=activity, proposals=[], downstream=None, source_available=current.source_available,
                standard_handoff=next((h for h in current.handoffs if h.run_id==run_id),None))
        return RunDetail(run=run, business_question='Reassess the recorded CR-017 validation result and remaining engineering review.'
            if (run.trigger.source_reference or '').startswith('evidence_') else host.event.request_summary,
            activity=activity, proposals=[p for p in snapshot.proposals if p.proposal.origin.run_id == run_id],
            downstream=snapshot.downstream, source_available=snapshot.source_available)

    @app.get('/control-api/cases/DR-009', response_model=DeliveryCaseView)
    def delivery_case(request: Request):
        actor(request).require_scope(*SCOPE)
        value=delivery.snapshot(host)
        if value is None: raise WorkflowError('DELIVERY_CASE_NOT_INSTALLED')
        return business_case(value)

    @app.post('/control-api/cases/DR-009/investigations', response_model=StartResponse, status_code=202)
    async def start_delivery(body: StartRequest, request: Request):
        selected=actor(request,True)
        if selected not in (AUTOMATION,ENGINEER,PROGRAM_OWNER):raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        if body.change_id!='DR-009':raise WorkflowError('CASE_SCOPE_MISMATCH')
        return await host.start(body,selected)

    @app.post('/control-api/delivery-commitment/review', response_model=DeliveryProgress)
    def review_delivery(body: DeliveryReviewRequest, request: Request):
        return host.delivery.review(body,actor(request,True))

    @app.post('/control-api/delivery-commitment/execute', response_model=DeliveryProgress)
    def execute_delivery(body: DeliveryActionRequest, request: Request):
        require_action(actor(request,True), 'DR-009', 'execute')
        return host.delivery.execute(body,AUTOMATION)

    @app.post('/control-api/delivery-commitment/reconcile', response_model=DeliveryProgress)
    def reconcile_delivery(body: DeliveryReconcileRequest, request: Request):
        return host.delivery.reconcile(body.run_id,actor(request,True))

    @app.get('/control-api/cases/QE-011', response_model=QualityCaseView)
    def autonomous_case(request: Request):
        actor(request).require_scope(*SCOPE)
        value = quality.snapshot(host, 'QE-011')
        if value is None: raise WorkflowError('CASE_NOT_FOUND')
        return business_case(value)

    @app.get('/control-api/cases/QE-004', response_model=QualityCaseView)
    def quality_case(request: Request):
        actor(request).require_scope(*SCOPE)
        value=quality.snapshot(host)
        if value is None: raise WorkflowError('QUALITY_CASE_NOT_INSTALLED')
        return business_case(value)

    @app.post('/control-api/cases/QE-004/investigations', response_model=StartResponse, status_code=202)
    async def start_quality(body: StartRequest, request: Request):
        selected=actor(request,True)
        if selected not in (AUTOMATION,ENGINEER,PROGRAM_OWNER):raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        if body.change_id!='QE-004':raise WorkflowError('CASE_SCOPE_MISMATCH')
        return await host.start(body,selected)

    @app.post('/control-api/quality-recovery/review', response_model=QualityProgress)
    def review_quality(body: QualityReviewRequest, request: Request):
        return host.quality.review(body,actor(request,True))

    @app.post('/control-api/quality-recovery/submit', response_model=QualityProgress)
    def submit_quality(body: QualitySubmissionRequest, request: Request):
        selected=actor(request,True)
        require_action(selected, 'QE-004', 'escalate')
        return host.quality.submit(body,selected)

    @app.post('/control-api/quality-recovery/execute', response_model=QualityProgress)
    def execute_quality(body: QualityActionRequest, request: Request):
        require_action(actor(request,True), 'QE-004', 'execute')
        return host.quality.execute(body,AUTOMATION)

    @app.post('/control-api/quality-recovery/reconcile', response_model=QualityProgress)
    def reconcile_quality(body: QualityReconcileRequest, request: Request):
        return host.quality.reconcile(body.run_id,actor(request,True))

    @app.get('/control-api/cases/CR-019', response_model=StandardCaseView)
    def standard_case(request: Request):
        actor(request).require_scope(*SCOPE)
        value = standard_change.snapshot(host)
        if value is None: raise WorkflowError('STANDARD_CASE_NOT_INSTALLED')
        return business_case(value)

    @app.post('/control-api/cases/CR-019/investigations', response_model=StartResponse, status_code=202)
    async def start_standard(body: StartRequest, request: Request):
        selected = actor(request, True)
        if selected not in (AUTOMATION, ENGINEER): raise WorkflowError('EXECUTION_ROLE_FORBIDDEN')
        if body.change_id != 'CR-019': raise WorkflowError('CASE_SCOPE_MISMATCH')
        return await host.start(body, selected)

    @app.post('/control-api/standard-handoffs/reconcile', response_model=StandardHandoff)
    def reconcile_standard(body: HandoffActionRequest, request: Request):
        return host.standard.recover(body, actor(request, True))

    @app.post('/control-api/standard-handoffs/retry', response_model=StandardHandoff)
    def retry_standard(body: HandoffActionRequest, request: Request):
        return host.standard.recover(body, actor(request, True), retry=True)

    @app.get('/control-api/automations', response_model=list[AutomationView])
    def automations(request: Request):
        require_surface(actor(request), 'workflows')
        return host.automations.list(actor(request))

    @app.get('/control-api/automations/{automation_id}', response_model=AutomationView)
    def automation(automation_id: str, request: Request):
        require_surface(actor(request), 'workflows')
        return host.automations.read(automation_id, actor(request))

    @app.post('/control-api/automations', response_model=AutomationView, status_code=201)
    def create_automation(body: CreateAutomation, request: Request):
        return host.automations.mutate('create', body, actor(request, True))

    @app.post('/control-api/automations/{automation_id}/update', response_model=AutomationView)
    def update_automation(automation_id: str, body: UpdateAutomation, request: Request):
        return host.automations.mutate('update', body, actor(request, True), automation_id)

    @app.post('/control-api/automations/{automation_id}/state', response_model=AutomationView)
    def configuration_state(automation_id: str, body: ChangeConfigurationState, request: Request):
        return host.automations.mutate('state', body, actor(request, True), automation_id)

    @app.post('/control-api/automations/{automation_id}/delete', response_model=DeletedAutomation)
    def delete_automation(automation_id: str, body: DeleteAutomation, request: Request):
        host.automations.mutate('delete', body, actor(request, True), automation_id)
        return {'deleted': True, 'automation_id': automation_id}

    from .concierge import attach
    attach(app, host, actor, {
        'cr017_review': (ReviewRequest, review), 'cr017_execute': (ExactRequest, execute),
        'quality_review': (QualityReviewRequest, review_quality), 'quality_execute': (QualityActionRequest, execute_quality),
        'delivery_review': (DeliveryReviewRequest, review_delivery), 'delivery_execute': (DeliveryActionRequest, execute_delivery),
        'automation_save': (CreateAutomation, create_automation),
    }, {'CR-017': start, 'CR-019': start_standard, 'QE-004': start_quality, 'DR-009': start_delivery})
    from .operations import attach as attach_operations
    attach_operations(app, host, actor)
    from .demo_management import attach as attach_demo_management
    attach_demo_management(app, host)
    return app
