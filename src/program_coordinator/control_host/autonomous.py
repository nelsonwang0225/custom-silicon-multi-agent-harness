"""One demo-entry/replay event -> existing shared workflow invocation.

No service-start replay, generic webhook, scheduler, business authority or model tools.
The source publishes atomically; independent HTTP readback validates dispatch.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

import httpx
from fastapi import Request
from starlette.concurrency import run_in_threadpool
from pydantic import Field
from enterprise_api.quality_events import QualitySourceEvent
from ..models import Model
from ..application.models import WorkflowError, Trigger, now_utc
from ..application.contracts import digest
from ..application.demo_identity import AUTOMATION
from ..application.store import ActivityStore
from .models import StartRequest
from .demo_models import DemoResetRequest
from .demo_management import durable_json
from .concurrency import settled_thread

DELAY_SECONDS = 8
WORKFLOW = 'yield_exception_recovery'


class AutonomousState(Model):
    status: Literal['idle','armed','event_emitted','workflow_running','touchless_handoff_verified','escalated','human_handoff_ready','failed'] = 'idle'
    generation: str | None = None
    epoch: str | None = None
    armed_at: str | None = None
    due_at: str | None = None
    delay_seconds: Literal[8] = DELAY_SECONDS
    event: QualitySourceEvent | None = None
    run_id: str | None = None
    error_code: str | None = None
    message: str = 'Autonomous opening idle.'


class AutonomousRequest(Model):
    expected_epoch: str = Field(min_length=1, max_length=80)


class AutonomousOpening:
    def __init__(self, host, management, *, sleep=asyncio.sleep):
        self.host, self.management, self.sleep = host, management, sleep
        self.path = host.store.directory / 'autonomous-opening.json'
        self.timer = None
        self.entry_lock = asyncio.Lock()

    def state(self):
        ActivityStore._safe_file(self.path)
        return AutonomousState.model_validate_json(self.path.read_text()) if self.path.exists() else AutonomousState()

    def save(self, value):
        durable_json(self.path, value.model_dump(mode='json'))

    def startup(self):
        original = self.state()
        # A run may have completed after the last controller snapshot. Reconcile
        # that durable run before classifying a host restart as interruption.
        state = self.status() if original.run_id else original.model_copy(deep=True)
        if state.status in {'armed','event_emitted','workflow_running'}:
            state.status, state.error_code = 'failed', 'HOST_INTERRUPTED'
            state.message = 'Interrupted opening; explicitly reset and prepare to replay.'
        if state != original:
            self.save(state)

    def status(self):
        state = self.state()
        if state.run_id:
            with self.host.store.transaction() as data:
                run = data.runs.get(state.run_id)
                progress = data.quality_recoveries.get(state.run_id)
            if run:
                if run.status == 'running':
                    state.status, state.error_code, state.message = 'workflow_running', None, 'Agents investigating QE-011.'
                elif run.status == 'completed' and progress and progress.status == 'handoff_verified':
                    state.status, state.error_code, state.message = 'touchless_handoff_verified', None, 'Quality investigation handoff verified. Lot remains on hold; no human approval required for executed actions.'
                elif run.status == 'completed' and progress and progress.status == 'review_required':
                    state.status, state.error_code, state.message = 'escalated', progress.error_code, 'Standard policy ineligible; review required. No autonomous handoff performed.'
                elif run.status == 'completed' and progress and progress.status == 'awaiting_review':
                    state.status, state.error_code, state.message = 'human_handoff_ready', None, 'Human decision required · Awaiting Program Owner.'
                elif run.status == 'completed' and progress and progress.status in {'approved','rejected','verified'}:
                    state.status, state.error_code = 'human_handoff_ready', None
                    state.message = 'Investigation complete · Human decision recorded · '+progress.status.replace('_',' ')+'.'
                elif run.status in {'failed','cancelled'} or not progress:
                    state.status, state.error_code = 'failed', run.error_code or 'HUMAN_HANDOFF_NOT_READY'
                    state.message = 'Investigation incomplete; inspect the current run.'
                elif run.status == 'completed':
                    state.status, state.error_code = 'failed', progress.error_code or 'HUMAN_HANDOFF_NOT_READY'
                    state.message = 'Investigation recorded; handoff needs attention. Inspect the current source state.'
        if not state.run_id and state.status in {'armed','event_emitted'} and self.timer is None:
            state.status, state.error_code = 'failed', 'AUTONOMOUS_STOPPED'
            state.message = 'Pending opening stopped; explicitly reset and prepare to replay.'
        return state

    async def stop(self):
        # Called before source reset while exclusive host admission is held.
        # Await cancellation so no timer or source-writing postprocessor survives.
        if self.timer:
            self.timer.cancel()
            await asyncio.gather(self.timer, return_exceptions=True)
            self.timer = None
        with self.host.store.transaction() as data:
            ids = {r.run_id for r in data.runs.values() if data.cases[r.case_id].change_id == 'QE-011'}
        tasks = [t for rid, t in self.host.run_tasks.items() if rid in ids]
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def cleared(self):
        previous = self.state()
        if previous.generation:
            durable_json(self.host.store.directory/'demo-archives'/('autonomous_'+uuid4().hex)/'event.json', previous.model_dump(mode='json'), immutable=True)
        self.save(AutonomousState())

    async def reset(self, body):
        if body.expected_epoch != self.management.state().epoch: raise WorkflowError('DEMO_STATE_CHANGED')
        await self.stop()
        value = await run_in_threadpool(self.management.reset, DemoResetRequest(scope='QE-011', confirmation='RESET', expected_epoch=body.expected_epoch))
        if not value.validation.baseline_valid: raise WorkflowError('DEMO_BASELINE_INVALID')
        return self.status()

    async def prepare(self, body):
        await self.reset(body)
        # Verify the existing main demo before arming; never restore it here.
        valid = await run_in_threadpool(self.management.verify)
        if not valid.baseline_valid: raise WorkflowError('DEMO_BASELINE_INVALID')
        return await self.arm()

    async def enter(self, body):
        # Entries share the normal request lease; only this narrow lock serializes
        # them, so normal reads/persona changes remain available during entry.
        async with self.entry_lock:
            return await self._enter(body)

    async def _enter(self, body):
        # Reset drains the request lease before restoring source records. Entry never
        # resets records, interrupts work, or replays a completed/failed opening.
        if body.expected_epoch != self.management.state().epoch:
            raise WorkflowError('DEMO_STATE_CHANGED')
        if self.management.state().recovery_required:
            raise WorkflowError('DEMO_RESET_RECONCILIATION_REQUIRED')
        state = self.status()
        if state.status != 'idle':
            return state
        valid = await run_in_threadpool(self.management.verify, 'QE-011')
        if not valid.baseline_valid:
            raise WorkflowError('DEMO_BASELINE_INVALID')
        return await self.arm(entry_epoch=body.expected_epoch)

    async def arm(self, *, entry_epoch=None):
        from .readiness import observe
        ready = await run_in_threadpool(observe, self.host)
        if not ready['runtime_invocable'] or (self.host.runtime_mode('QE-011') == 'live_model' and not ready['model_configuration']['credential_present']):
            raise WorkflowError('AUTONOMOUS_RUNTIME_UNAVAILABLE')
        if entry_epoch is not None:
            if self.management.resetting:
                raise WorkflowError('DEMO_RESET_BUSY')
            if self.management.state().epoch != entry_epoch:
                raise WorkflowError('DEMO_STATE_CHANGED')
        generation = 'quality_event_' + uuid4().hex
        now = datetime.now(timezone.utc)
        value = AutonomousState(status='armed', generation=generation, epoch=self.management.state().epoch,
            armed_at=now.isoformat().replace('+00:00','Z'),
            due_at=(now+timedelta(seconds=DELAY_SECONDS)).isoformat().replace('+00:00','Z'),
            message='QE-011 starts automatically in 8 seconds from a Manufacturing event.')
        self.save(value)
        self.timer = asyncio.create_task(self.emit_after_delay(generation))
        return value

    def read_event(self, event_id):
        try:
            r = self.host.source._http.get(self.host.source.config.base_url+'/api/v1/manufacturing/quality-events/'+event_id,
                headers={'Authorization':'Bearer '+self.host.source.config.reader_identity}, follow_redirects=False)
            if r.status_code != 200: raise WorkflowError('SOURCE_EVENT_UNAVAILABLE')
            return QualitySourceEvent.model_validate(r.json())
        except (httpx.HTTPError, ValueError):
            raise WorkflowError('SOURCE_EVENT_UNAVAILABLE') from None

    async def dispatch(self, event):
        event = QualitySourceEvent.model_validate(event)
        state = self.state()
        if (state.generation != event.event_id or state.epoch != self.management.state().epoch
                or state.status not in {'event_emitted','workflow_running'}):
            raise WorkflowError('EVENT_NOT_ARMED')
        authoritative = await run_in_threadpool(self.read_event, event.event_id)
        if authoritative != event: raise WorkflowError('SOURCE_EVENT_MISMATCH')
        context = await run_in_threadpool(self.host.quality.context, 'QE-011')
        if (context.context_digest != event.context_digest or context.exception.content_version != event.source_record_version
                or context.exception.lot_id != event.lot_id or context.exception.updated_at != event.source_record_updated_at):
            raise WorkflowError('STALE_SOURCE_EVENT')
        key = 'ui_event_' + digest([event.event_id, event.event_version, WORKFLOW])[:48]
        # SAME admission, WorkflowService, CaseHarness and QualityRecoveryService
        # as manual quality invocation. No alternate runtime or fake activity.
        result = await self.host.start(StartRequest(invocation_id=key, workflow_id=WORKFLOW, change_id='QE-011'), AUTOMATION,
            expected_quality_digest=event.context_digest,
            trigger=Trigger(kind='source_event', source_reference=event.event_id,
                event_name=event.event_name, event_version=event.event_version))
        state.run_id, state.status = result['run_id'], 'workflow_running'
        state.message = 'Agents investigating QE-011.'
        self.save(state)
        return result

    async def emit_after_delay(self, generation):
        try:
            await self.sleep(DELAY_SECONDS)
            async with self.management.request_lease():
                state = self.state()
                if state.generation != generation or state.status != 'armed' or state.epoch != self.management.state().epoch:
                    return
                self.management.binding()
                from mock_enterprise.autonomous_quality import publish
                event = await settled_thread(publish, self.management.settings, generation, now_utc(), state.epoch)
                state.event, state.status, state.message = event, 'event_emitted', 'Manufacturing source event emitted.'
                self.save(state)
                # A reset already draining this lease must never race into a
                # fresh paid invocation after its source publication finishes.
                if self.management.resetting: return
                await self.dispatch(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            state = self.state()
            if state.generation == generation:
                state.status = 'failed'
                state.error_code = str(exc) if isinstance(exc, WorkflowError) else 'AUTONOMOUS_EVENT_FAILED'
                state.message = 'Autonomous opening failed; inspect Operations, then explicitly reset to replay.'
                self.save(state)


def attach(app, host, management):
    service = AutonomousOpening(host, management)
    host.autonomous = service

    def maintainer(request):
        if request.headers.get('x-stratos-demo-maintainer') != 'local-demo-reset' or request.headers.get('x-stratos-demo-profile') != 'automation':
            raise WorkflowError('DEMO_MAINTAINER_REQUIRED')

    @app.get('/control-api/demo/autonomous', response_model=AutonomousState)
    def status(request: Request):
        from .access import resolve_actor, require_surface
        require_surface(resolve_actor(request), 'operations')
        return service.status()

    @app.post('/control-api/demo/autonomous/prepare', response_model=AutonomousState)
    async def prepare(body: AutonomousRequest, request: Request):
        maintainer(request)
        return await service.prepare(body)

    @app.post('/control-api/demo/autonomous/enter', response_model=AutonomousState)
    async def enter(body: AutonomousRequest, request: Request):
        # Explicitly authorized local demo lifecycle, independent of the viewer's
        # business persona. It grants no review, reset, or generic write authority.
        from .access import resolve_actor, require_surface
        require_surface(resolve_actor(request), 'overview')
        return await service.enter(body)

    @app.post('/control-api/demo/autonomous/reset', response_model=AutonomousState)
    async def reset(body: AutonomousRequest, request: Request):
        maintainer(request)
        return await service.reset(body)
