"""Host-only administrative adapter. No model, MCP or business write entry point."""
import asyncio
from contextlib import asynccontextmanager, contextmanager
import json
import os
import time
from uuid import uuid4

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse

from mock_enterprise.demo_management import (VERSION, SCENARIOS, SYSTEMS, storage_id,
    scope_cases, maintenance_lock, inspect_source, restore_source, finish_source_reset)
from ..application.models import WorkflowError, now_utc
from ..application.contracts import digest
from ..application.store import ActivityStore
from ..application.automations import example_definitions
from .demo_models import (DemoScope, DemoState, DemoControls, DemoPreview, DemoResetRequest,
    DemoResetResult, DemoAudit, BaselineCheck)

SCOPE = ('CUST-FML01','PRG-A17')


@contextmanager
def maintenance_window(settings, *, attempts=50, interval=.05):
    """Wait briefly for ordinary source reads to release their shared lease."""
    lease = None
    for attempt in range(attempts):
        candidate = maintenance_lock(settings, exclusive=True)
        try:
            candidate.__enter__()
            lease = candidate
            break
        except ValueError as exc:
            if str(exc) != 'DEMO_MAINTENANCE_BUSY' or attempt == attempts - 1:
                raise
            time.sleep(interval)
    try:
        yield
    finally:
        if lease is not None:
            lease.__exit__(None, None, None)


def durable_json(path, value, *, immutable=False):
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise WorkflowError('UNSAFE_DEMO_STORAGE')
    ActivityStore._safe_file(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    encoded = json.dumps(value, sort_keys=True, indent=2) + '\n'
    temp = path.with_name('demo-' + uuid4().hex + '.tmp')
    try:
        with os.fdopen(os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as f:
            f.write(encoded); f.flush(); os.fsync(f.fileno())
        if immutable:
            # No replacement of an existing archived snapshot, even on retry.
            os.link(temp, path)
        else:
            os.replace(temp, path)
        fd = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


def belongs(record, case_ids, run_ids):
    for r in (record, getattr(record,'origin',None), getattr(record,'reference',None)):
        if r is not None and (getattr(r,'case_id',None) in case_ids or getattr(r,'run_id',None) in run_ids):
            return True
    return False


def prune_index(data, scope):
    """Explicit ownership selection; never wipe an arbitrary store/table."""
    cases = scope_cases(scope)
    case_ids = {c.case_id for c in data.cases.values() if (c.customer_id,c.program_id)==SCOPE and c.change_id in cases}
    run_ids = {r.run_id for r in data.runs.values() if r.case_id in case_ids}
    proposal_keys = {k for k,p in data.proposals.items() if belongs(p,case_ids,run_ids)}
    for name in ('proposals','decisions','actions','verifications','preparations','reviews','executions',
                 'standard_handoffs','quality_recoveries','delivery_commitments','operator_escalations'):
        values = getattr(data,name)
        setattr(data,name,{k:v for k,v in values.items() if not belongs(v,case_ids,run_ids)})
    data.proposal_status = {k:v for k,v in data.proposal_status.items() if k not in proposal_keys}
    data.execution_attempts = [v for v in data.execution_attempts if not belongs(v,case_ids,run_ids)]
    data.activity = [v for v in data.activity if not belongs(v,case_ids,run_ids)]
    data.runs = {k:v for k,v in data.runs.items() if k not in run_ids}
    data.cases = {k:v for k,v in data.cases.items() if k not in case_ids}
    for key,s in list(data.concierge_sessions.items()):
        if (s.customer_id,s.program_id)!=SCOPE:
            continue
        touched = bool(set(s.run_ids)&run_ids) or any(any(case in (t.context + ' ' + ' '.join(c.title for c in t.cards)) for case in cases) for t in s.turns)
        if scope=='full' or touched:
            del data.concierge_sessions[key]


class DemoManagement:
    def __init__(self, host, settings):
        settings.validate(existing=True)
        from mock_enterprise.config import PROJECT
        directory = host.store.directory.absolute()
        if (not any(directory.is_relative_to(PROJECT/name) for name in ('.demo','.cache'))
                or any(p.is_symlink() for p in (directory,*directory.parents))):
            raise WorkflowError('UNSAFE_DEMO_STORAGE')
        self.host, self.settings = host, settings
        self.path = host.store.directory / 'demo-management.json'
        self.condition = asyncio.Condition()
        self.active_requests = 0
        self.resetting = False
        # No startup seeding/restoration. A persisted interrupted journal remains
        # recovery-required after process restart until an explicit retry.

    @asynccontextmanager
    async def request_lease(self, *, reset=False, wait_reset=False):
        # Normal HTTP reads remain concurrent. Only reset drains in-flight host
        # requests, then rejects new arrivals while the maintenance lease is held.
        async with self.condition:
            if self.resetting:
                if not wait_reset:
                    raise WorkflowError('DEMO_RESET_BUSY')
                try:
                    await asyncio.wait_for(self.condition.wait_for(lambda: not self.resetting), timeout=15)
                except TimeoutError:
                    raise WorkflowError('DEMO_RESET_BUSY') from None
            if reset:
                self.resetting = True
                try:
                    await asyncio.wait_for(self.condition.wait_for(lambda: self.active_requests==0),timeout=15)
                except BaseException:
                    self.resetting = False
                    self.condition.notify_all()
                    raise
            else:
                self.active_requests += 1
        try:
            yield
        finally:
            async with self.condition:
                if reset: self.resetting = False
                else: self.active_requests -= 1
                self.condition.notify_all()

    def state(self):
        ActivityStore._safe_file(self.path)
        return DemoState.model_validate_json(self.path.read_text()) if self.path.exists() else DemoState()

    def save(self, state):
        durable_json(self.path, state.model_dump(mode='json'))

    def controls(self):
        s = self.state()
        return DemoControls(enabled=True,epoch=s.epoch,recovery_required=s.recovery_required,
            pending_scope=s.pending_scope,scopes=['full',*SCENARIOS,'QE-011'],latest=s.audit[-1] if s.audit else None,
            archived_reset_count=sum(a.result in ('restored','partial') for a in s.audit))

    def binding(self):
        # Server-selected file MUST be the running source behind this HTTP URL.
        # Health headers disclose a one-way storage identifier, never a path.
        try:
            r = self.host.source._http.get(self.host.source.config.base_url+'/health')
            if r.status_code!=200:
                raise WorkflowError('DEMO_SOURCE_UNAVAILABLE')
            if (r.headers.get('x-stratos-demo-storage'),r.headers.get('x-stratos-demo-protocol')) != (storage_id(self.settings),VERSION):
                raise WorkflowError('DEMO_SOURCE_BINDING_MISMATCH')
        except httpx.HTTPError:
            raise WorkflowError('DEMO_SOURCE_UNAVAILABLE') from None

    def preview(self, scope):
        state = self.state()
        self.binding()
        checked = inspect_source(self.settings,scope)
        cases = scope_cases(scope)
        from mock_enterprise.demo_management import baseline
        _, owners = baseline()
        systems = sorted({kind.split('.')[0] for (kind,rid),s in owners.items() if s&cases})
        if 'QE-011' in cases: systems=sorted(set(systems)|{'manufacturing','erp','planner'})
        reasons = checked['conflicts']
        if scope != 'full' and any('scenario clock' in d for d in checked['discrepancies']):
            reasons = [*reasons, 'The shared source clock changed; use Full Demo Reset.']
        if state.recovery_required and scope not in ('full',state.pending_scope):
            reasons = [*reasons,'An incomplete reset requires the same scope or Full Demo Reset.']
        return DemoPreview(scope=scope,epoch=state.epoch,affected_systems=systems,allowed=not reasons,discrepancies=reasons,
            resets=['Canonical source records for '+', '.join(sorted(cases)),
                    'Selected demo runs, proposals, decisions, attempts, verification and activity are archived',
                    'Current conversational drafts/actions are invalidated; affected visible history is archived',
                    'Temporary scoped automation configurations; curated examples restored'],
            preserves=['Historical Phase 07 4/6 failures and later targeted passes',
                       'Existing trace/eval files and documentation', 'Workflow definitions and product configuration',
                       'Unrelated source records and case history; all schedules remain inactive'],
            shared_dependencies=['QE-004 and DR-009 share held/released material and ORD-HEL-800 / MS-HEL-800.',
                'CR-017 and CR-019 share validation inputs; DR-009 may reference CR-017 technical readiness.',
                'Full reset restores all shared facts. A conflicting single-case reset is refused.'])

    def busy(self, scope='full'):
        if (scope == 'full' and self.host.tasks) or self.host.concierge.tasks:
            return True
        with self.host.store.transaction() as data:
            return any((r.status=='running' or r.run_id in self.host.run_tasks) and (r.customer_id,r.program_id)==SCOPE
                and data.cases[r.case_id].change_id in scope_cases(scope) for r in data.runs.values())

    async def stop_demo_work(self):
        """Explicit master restart only, under the exclusive request lease.

        Drain owned work before restoring sources. Unrelated work is preserved
        and the existing busy check still refuses an unsafe reset.
        """
        with self.host.store.transaction() as data:
            sessions = {s.session_id for s in data.concierge_sessions.values()
                        if (s.customer_id, s.program_id) == SCOPE}
        chat_tasks = [t for (session, _), t in self.host.concierge.tasks.items() if session in sessions]
        for task in chat_tasks:
            task.cancel()
        await asyncio.gather(*chat_tasks, return_exceptions=True)
        await self.host.autonomous.stop()
        with self.host.store.transaction() as data:
            ids = {r.run_id for r in data.runs.values() if (r.customer_id, r.program_id) == SCOPE
                   and data.cases[r.case_id].change_id in scope_cases('full')}
        tasks = [t for rid, t in self.host.run_tasks.items() if rid in ids]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def reconcile(self, scope, archive):
        with self.host.store.transaction(write=True) as data:
            archive('host', {'category':'archived_demo_orchestration','scope':scope,'index':data.model_dump(mode='json')})
            prune_index(data,scope)
        with self.host.automations.transaction(write=True) as data:
            archive('automations', {'category':'archived_demo_configuration','scope':scope,'index':data.model_dump(mode='json')})
            cases = scope_cases(scope)
            selected = {k for k,v in data.definitions.items() if (v.customer_id,v.program_id)==SCOPE and (scope=='full' or v.case_scope in cases)}
            examples = example_definitions()
            selected |= {k for k,v in examples.items() if scope=='full' or v.case_scope in cases}
            # Include deleted scoped definitions using their exact saved receipts.
            selected |= {r.automation_id for r in data.receipts.values() if r.result and
                         (r.result.customer_id,r.result.program_id)==SCOPE and (scope=='full' or r.result.case_scope in cases)}
            data.definitions = {k:v for k,v in data.definitions.items() if k not in selected}
            data.definitions.update({k:v for k,v in examples.items() if k in selected})
            data.receipts = {k:v for k,v in data.receipts.items() if v.automation_id not in selected}
            data.activity = [v for v in data.activity if v.automation_id not in selected]
            if scope=='full': data.examples_seeded = True
        self.host.concierge.turns.clear()
        self.host.concierge.actions.clear()
        self.host.concierge.receipts.clear()
        self.host.operations_health = None

    def verify(self, scope='full', *, allow_pending=False):
        discrepancies, observations = [], {}
        scenario_checks = {}
        source = {}
        try:
            self.binding()
            source = inspect_source(self.settings,scope)
            discrepancies.extend(source['discrepancies'])
            if source['reset_pending'] and not allow_pending:
                discrepancies.append('Source maintenance barrier requires explicit reset reconciliation')
            # Independent source HTTP reads, through the existing adapters.
            for system, method, args in (
                ('engineering','get_change_request',('CR-017',)),
                ('validation','get_validation_coverage',('CR-017',)),
                ('manufacturing','get_manufacturing_lots',('PRG-A17',)),
                ('erp','get_customer_order',('ORD-HEL-800',)),
                ('planner','get_program',('PRG-A17',))):
                try:
                    getattr(self.host.source.read,method)(*args)
                    observations[system] = 'read_succeeded'
                except WorkflowError:
                    observations[system] = 'unavailable'
                    discrepancies.append(system+': independent source read failed')
            for case in sorted(scope_cases(scope)-{'QE-011'}):
                try:
                    scenario_checks[case] = self.verify_scenario_http(case)
                except (WorkflowError,ValueError,KeyError,TypeError):
                    scenario_checks[case] = False
                if not scenario_checks[case]:
                    discrepancies.append(case+': independent HTTP state does not match the baseline')
            if scope == 'QE-011':
                scenario_checks['QE-011'] = not source['discrepancies']
            again = inspect_source(self.settings,scope)
            if again['source_digest'] != source['source_digest']:
                discrepancies.append('Source state changed during baseline verification; retry')
        except (WorkflowError,ValueError,OSError):
            discrepancies.append('Authoritative source baseline unavailable; retry/reconcile required')
        with self.host.store.transaction() as data:
            after = data.model_copy(deep=True)
            prune_index(after,scope)
            if after != data:
                discrepancies.append('Current scoped control-plane runs, approval/action state or Concierge history remain')
            control_digest = digest(after.model_dump(mode='json'))
        with self.host.automations.transaction() as data:
            examples = example_definitions()
            for key,value in examples.items():
                if (scope=='full' or value.case_scope in scope_cases(scope)) and data.definitions.get(key)!=value:
                    discrepancies.append('Curated automation configuration differs: '+key)
            if any(not a.seeded_example and (a.customer_id,a.program_id)==SCOPE and (scope=='full' or a.case_scope in scope_cases(scope)) for a in data.definitions.values()):
                discrepancies.append('Temporary scoped automation configurations remain')
        if self.host.concierge.actions or (scope=='full' and self.host.concierge.turns):
            discrepancies.append('Current Concierge conversation/action state remains')
        if self.state().recovery_required and not allow_pending:
            discrepancies.append('Reset journal requires explicit retry/reconciliation')
        return BaselineCheck(scope=scope,baseline_valid=not discrepancies,checked_at=now_utc(),
            discrepancies=discrepancies,quantities=source.get('quantities',{}),source_digest=source.get('source_digest'),
            control_digest=control_digest,source_readback=observations,scenario_checks=scenario_checks)

    def verify_scenario_http(self, case):
        """Assert current business projections, not merely successful HTTP status."""
        read = self.host.source.read
        if case=='CR-017':
            from .downstream import read_physical
            change, coverage = read.get_change_request(case), read.get_validation_coverage(case)
            physical = read_physical(self.host.source)
            return (change['workflow_state']=='pending_impact_assessment' and change['current_plan_id'] is None
                    and not coverage['coverage_satisfied'] and physical.available and physical.job is None
                    and physical.result is None and not physical.reviews and physical.customer_acceptance=='pending')
        if case=='CR-019':
            context = self.host.standard.context()
            return (context.change['workflow_state']=='new' and context.procedure['status']=='approved'
                    and not read.get_standard_validation_intakes(case)['items'])
        if case=='QE-004':
            context, records = self.host.quality.context(), self.host.quality.records()
            a = context.analysis
            return (context.exception.status=='open' and a.comparable=='true' and
                    (a.observed_rate_bps,a.baseline_rate_bps,a.held_quantity,a.affected_eligible_quantity,
                     a.eligible_quantity,a.requested_quantity,a.gap_quantity)==(8000,9600,250,0,600,800,200)
                    and not any((records.investigations,records.plans,records.decisions,records.tasks)))
        context, records = self.host.delivery.context(), self.host.delivery.records()
        a = context.analysis
        return ((a.physical_total,a.held_quantity,a.allocated_quantity,a.eligible_quantity,
                 a.requested_quantity,a.gap_quantity)==(1000,250,150,600,800,200)
                and a.technical_readiness=='READY' and a.inventory_consistent
                and context.request.customer_agreement=='pending' and context.request.technical_change_id is None
                and context.state.current_commitment_id is None
                and not any((records.plans,records.decisions,records.commitments,records.links)))

    def reset(self, body):
        state = self.state()
        if body.expected_epoch != state.epoch:
            raise WorkflowError('DEMO_STATE_CHANGED')
        preview = self.preview(body.scope)
        if not preview.allowed:
            raise WorkflowError('SHARED_DEPENDENCY_REQUIRES_FULL_RESET')
        if self.busy(body.scope):
            raise WorkflowError('DEMO_RESET_BUSY')
        audit = DemoAudit(reset_id=('reset_autonomous_' if body.scope=='QE-011' else 'reset_')+uuid4().hex,scope=body.scope,timestamp=now_utc(),result='started',stage='source_restore',affected_systems=preview.affected_systems)
        root = self.host.store.directory/'demo-archives'/audit.reset_id
        def archive(kind, value): durable_json(root/(kind+'.json'),value,immutable=True)
        with self.host.store.execution_lock():
            state.epoch = audit.reset_id
            state.recovery_required, state.pending_scope = True, body.scope
            state.audit.append(audit)
            self.save(state)
            check = None
            try:
                # Recheck after the durable admission barrier, closing the
                # concurrent local WorkflowService.claim race.
                if self.busy(body.scope):
                    raise WorkflowError('DEMO_RESET_BUSY')
                with maintenance_window(self.settings):
                    restore_source(self.settings,body.scope,archive=lambda v:archive('source',v),epoch=state.epoch)
                    audit.stage = 'host_reconciliation'
                    self.save(state)
                    self.reconcile(body.scope,archive)
                    if body.scope in {'full','QE-011'} and getattr(self.host,'autonomous',None):
                        self.host.autonomous.cleared()
                audit.stage = 'independent_validation'
                self.save(state)
                check = self.verify(body.scope,allow_pending=True)
                if not check.baseline_valid:
                    raise WorkflowError('DEMO_BASELINE_INVALID')
                audit.stage = 'source_resume'
                self.save(state)
                finish_source_reset(self.settings,state.epoch)
                audit.result, audit.stage, audit.baseline_valid = 'restored','complete',True
                state.recovery_required, state.pending_scope = False, None
            except Exception as exc:
                audit.result = 'failed' if audit.stage=='source_restore' else 'partial'
                audit.error_code = str(exc) if isinstance(exc,WorkflowError) else 'DEMO_RESET_STAGE_FAILED'
                if check is None:
                    check = BaselineCheck(scope=body.scope,baseline_valid=False,checked_at=now_utc(),
                        discrepancies=[audit.stage+': '+audit.error_code+'; explicit retry/reconciliation required'])
                elif check.baseline_valid:
                    check.baseline_valid = False
                    check.discrepancies.append(audit.stage+': '+audit.error_code+'; explicit retry/reconciliation required')
            self.save(state)
            return DemoResetResult(result=audit.result,epoch=state.epoch,audit=audit,validation=check)


def attach(app, host):
    service = getattr(host,'demo_management',None)

    @app.get('/control-api/demo',response_model=DemoControls)
    def controls():
        return service.controls() if service else DemoControls(enabled=False)

    if service is None:
        return
    from .autonomous import attach as attach_autonomous
    attach_autonomous(app, host, service)

    @app.get('/control-api/demo/preview',response_model=DemoPreview)
    def preview(scope: DemoScope):
        return service.preview(scope)

    @app.get('/control-api/demo/verify',response_model=BaselineCheck)
    def verify(scope: DemoScope = 'full'):
        return service.verify(scope)

    @app.post('/control-api/demo/reset',response_model=DemoResetResult)
    async def reset(body:DemoResetRequest,request:Request):
        # Separate explicit demo-maintainer selector: no business/agent profile
        # obtains reset authority. Outer host origin/CSRF guard applies too.
        if request.headers.get('x-stratos-demo-maintainer')!='local-demo-reset':
            raise WorkflowError('DEMO_MAINTAINER_REQUIRED')
        if request.headers.get('x-stratos-demo-profile') not in (None, 'automation'):
            raise WorkflowError('DEMO_MAINTAINER_REQUIRED')
        if body.restart_opening and request.headers.get('x-stratos-demo-profile') != 'automation':
            raise WorkflowError('DEMO_MAINTAINER_REQUIRED')
        if body.expected_epoch != service.state().epoch: raise WorkflowError('DEMO_STATE_CHANGED')
        # Validate source binding and scope before interrupting active work.
        from starlette.concurrency import run_in_threadpool
        if body.restart_opening:
            await run_in_threadpool(service.preview, body.scope)
            await service.stop_demo_work()
        elif body.scope in {'full','QE-011'}:
            await host.autonomous.stop()
        from .concurrency import settled_thread
        value = await settled_thread(service.reset,body)
        if body.restart_opening and value.validation.baseline_valid:
            try:
                await host.autonomous.arm()
                value.opening_status = 'armed'
            except Exception as exc:
                # A restored baseline and a failed opening are distinct outcomes.
                # Never retry a model invocation or report running agents here.
                value.opening_status = 'failed'
                value.opening_error = str(exc) if isinstance(exc, WorkflowError) else 'AUTONOMOUS_START_FAILED'
                opening = host.autonomous.state()
                opening.status, opening.error_code = 'failed', value.opening_error
                opening.message = 'Demo reset complete, but QE-011 could not start. Explicitly replay the autonomous opening to retry.'
                host.autonomous.save(opening)
        return JSONResponse(value.model_dump(mode='json'),status_code=200 if value.validation.baseline_valid else 503)
