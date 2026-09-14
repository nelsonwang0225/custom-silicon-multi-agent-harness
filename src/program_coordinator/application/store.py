"""Small host-owned JSON index alongside the existing per-trace JSON artifacts.

No source-system storage access. A POSIX file lock plus atomic replacement makes
invocation admission and metadata updates safe across local CLI processes. This is
an index/activity store, not another SDK session, runner, or event-sourcing system.
"""

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
from uuid import uuid4

from pydantic import Field
from ..models import Model
from .contracts import Proposal, DecisionBinding, ActionAttempt, VerificationRecord, Origin, digest, validate_proposal
from .models import CaseRecord, RunRecord, ActivityRecord, WorkflowError, now_utc
from .standard_handoff_models import StandardHandoff
from .quality_recovery_models import QualityProgress
from .delivery_models import DeliveryProgress
from .execution_models import Preparation, HumanReview, ExecutionRecord, ExecutionAttempt, OperatorEscalation


from .observability import ObservedSession


class MetadataIndex(Model):
    concierge_sessions: dict[str, ObservedSession] = Field(default_factory=dict)
    schema_version: int = 1
    cases: dict[str, CaseRecord] = Field(default_factory=dict)
    runs: dict[str, RunRecord] = Field(default_factory=dict)
    activity: list[ActivityRecord] = Field(default_factory=list)
    proposals: dict[str, Proposal] = Field(default_factory=dict)
    proposal_status: dict[str, str] = Field(default_factory=dict)
    decisions: dict[str, DecisionBinding] = Field(default_factory=dict)
    actions: dict[str, ActionAttempt] = Field(default_factory=dict)
    verifications: dict[str, VerificationRecord] = Field(default_factory=dict)
    preparations: dict[str, Preparation] = Field(default_factory=dict)
    reviews: dict[str, HumanReview] = Field(default_factory=dict)
    executions: dict[str, ExecutionRecord] = Field(default_factory=dict)
    execution_attempts: list[ExecutionAttempt] = Field(default_factory=list)
    delivery_commitments: dict[str, DeliveryProgress] = Field(default_factory=dict)
    quality_recoveries: dict[str, QualityProgress] = Field(default_factory=dict)
    standard_handoffs: dict[str, StandardHandoff] = Field(default_factory=dict)
    operator_escalations: dict[str, OperatorEscalation] = Field(default_factory=dict)


class ActivityStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        if self.directory.is_symlink():
            raise WorkflowError("UNSAFE_METADATA_STORAGE")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = self.directory / "workflow-index.json"

    @staticmethod
    def _safe_file(path):
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_nlink != 1)):
            raise WorkflowError("UNSAFE_METADATA_STORAGE")

    @contextmanager
    def execution_lock(self):
        """Serialize local review/revision/resume, releasing on process death.

        Separate from the short JSON transaction so started writes are durably
        recorded before HTTP. A competing CLI fails promptly instead of blocking.
        """
        path = self.directory / "execution.lock"
        self._safe_file(path)
        with os.fdopen(os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), "r+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise WorkflowError("EXECUTION_BUSY") from None
            yield

    @contextmanager
    def transaction(self, *, write=False):
        lock_path = self.directory / "workflow-index.lock"
        self._safe_file(lock_path)
        with os.fdopen(os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), "r+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self._safe_file(self.path)
            data = MetadataIndex.model_validate_json(self.path.read_text()) if self.path.exists() else MetadataIndex()
            if data.schema_version != 1:
                raise WorkflowError("UNSUPPORTED_METADATA_VERSION")
            yield data
            if write:
                encoded = data.model_dump_json(indent=2)
                MetadataIndex.model_validate_json(encoded)
                temp = self.directory / ("workflow-index-" + uuid4().hex + ".tmp")
                try:
                    with os.fdopen(os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as target:
                        target.write(encoded + "\n")
                        target.flush()
                        os.fsync(target.fileno())
                    os.replace(temp, self.path)
                    directory_fd = os.open(self.directory, os.O_RDONLY)
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
                finally:
                    temp.unlink(missing_ok=True)

    def _activity(self, data, run, kind, *, details=None, source_references=(), proposal_id=None, action_id=None, actor=None):
        data.activity.append(ActivityRecord(event_id="activity_" + uuid4().hex, timestamp=now_utc(),
            customer_id=run.customer_id, program_id=run.program_id, case_id=run.case_id, run_id=run.run_id,
            event_type=kind, actor_id=actor.actor_id if actor else run.actor_id,
            actor_source=actor.identity_source if actor else run.actor_source, trace_id=run.trace_id,
            details=details or {}, source_references=list(source_references), proposal_id=proposal_id, action_id=action_id))

    def claim(self, request, actor, *, execution_mode, trace_id=None, artifact_directory=None):
        actor.require_scope(request.customer_id, request.program_id)
        encoded_request = request.model_dump(mode="json")
        # Preserve existing invocation receipts when optional event provenance is absent.
        for key in ('event_name','event_version'):
            if encoded_request['trigger'].get(key) is None: encoded_request['trigger'].pop(key,None)
        request_hash = digest({"request": encoded_request, "actor_id": actor.actor_id,
                               "execution_mode": execution_mode})
        with self.transaction(write=True) as data:
            # An explicit demo reset is a separate host operation. The durable
            # marker also closes admission from a concurrent local CLI process.
            reset_state = self.directory / 'demo-management.json'
            self._safe_file(reset_state)
            if reset_state.exists():
                import json
                if json.loads(reset_state.read_text()).get('recovery_required'):
                    raise WorkflowError('DEMO_RESET_RECONCILIATION_REQUIRED')
            prior = next((r for r in data.runs.values() if r.invocation_id == request.invocation_id), None)
            if prior:
                actor.require_scope(prior.customer_id, prior.program_id)
                if prior.request_digest != request_hash:
                    raise WorkflowError("INVOCATION_ID_CONFLICT")
                return prior, True
            intake_key = digest([request.customer_id, request.program_id,
                request.event.change_id or ("incomplete_event:" + request.event.event_id)])
            case = data.cases.get(request.case_id) if request.case_id else next(
                (c for c in data.cases.values() if c.intake_key == intake_key), None)
            if request.case_id and case is None:
                raise WorkflowError("CASE_NOT_FOUND")
            if case and (case.customer_id != request.customer_id or case.program_id != request.program_id
                         or case.intake_key != intake_key):
                raise WorkflowError("CASE_SCOPE_MISMATCH")
            created = case is None
            if created:
                case = CaseRecord(case_id="case_" + uuid4().hex, customer_id=request.customer_id,
                    program_id=request.program_id, change_id=request.event.change_id, intake_key=intake_key, created_at=now_utc())
                data.cases[case.case_id] = case
            run = RunRecord(run_id="run_" + uuid4().hex, case_id=case.case_id, customer_id=case.customer_id,
                program_id=case.program_id, workflow_id=request.workflow_id, definition_version=request.definition_version,
                invocation_id=request.invocation_id, request_digest=request_hash, correlation_id=request.event.correlation_id,
                actor_id=actor.actor_id, actor_source=actor.identity_source, trigger=request.trigger,
                trace_id=trace_id, execution_mode=execution_mode, started_at=now_utc(), artifact_directory=artifact_directory)
            data.runs[run.run_id] = run
            if created:
                self._activity(data, run, "case_created")
            self._activity(data, run, "analysis_started", details={"execution_mode": execution_mode})
            return run, False

    def finish(self, run_id, *, state=None, error_code=None, cancelled=False):
        with self.transaction(write=True) as data:
            run = data.runs[run_id]
            if run.status != "running":
                raise WorkflowError("RUN_ALREADY_FINISHED")
            if state is not None:
                if (state.case_id != run.case_id or state.run_id != run.run_id
                        or state.workflow_id != run.workflow_id or state.workflow_definition_version != run.definition_version
                        or state.workflow_stage != "completed" or state.final_package_status != "validated"
                        or not state.final_package or state.final_package.case_id != run.case_id):
                    raise WorkflowError("INVALID_ANALYSIS_RESULT")
                for field in ("customer_id", "program_id"):
                    # An unscoped intake may yield an explicit escalation package.
                    actual = getattr(state.final_package, field)
                    if actual is not None and actual != getattr(run, field):
                        raise WorkflowError("RESULT_SCOPE_MISMATCH")
                    if actual is None and state.final_package.policy_path != "escalation_required":
                        raise WorkflowError("RESULT_SCOPE_MISMATCH")
                if not state.scope_verified and state.final_package.policy_path != "escalation_required":
                    raise WorkflowError("RESULT_SCOPE_UNVERIFIED")
                run.status = "completed"
                run.recommendation = state.final_package
                data.cases[run.case_id].scope_verified |= state.scope_verified
                self._activity(data, run, "analysis_completed", details={"policy_path": state.final_package.policy_path})
                self._activity(data, run, "recommendation_recorded", source_references=state.source_references,
                    details={"policy_path": state.final_package.policy_path, "business_actions_executed": False})
            else:
                run.status = "cancelled" if cancelled else "failed"
                run.error_code = error_code or "ANALYSIS_FAILED"
                self._activity(data, run, "analysis_cancelled" if cancelled else "analysis_failed", details={"error_code": run.error_code})
            run.completed_at = now_utc()
            return run

    def cases(self, actor, *, customer_id, program_id):
        actor.require_scope(customer_id, program_id)
        with self.transaction() as data:
            return [c for c in data.cases.values() if c.customer_id == customer_id and c.program_id == program_id]

    def runs(self, actor, *, customer_id, program_id, case_id=None):
        actor.require_scope(customer_id, program_id)
        with self.transaction() as data:
            return [r for r in data.runs.values() if r.customer_id == customer_id and r.program_id == program_id
                    and (case_id is None or r.case_id == case_id)]

    def timeline(self, actor, *, customer_id, program_id, case_id=None, run_id=None):
        actor.require_scope(customer_id, program_id)
        with self.transaction() as data:
            return [e for e in data.activity if e.customer_id == customer_id and e.program_id == program_id
                    and (case_id is None or e.case_id == case_id) and (run_id is None or e.run_id == run_id)]

    def retain(self, record, actor):
        """Trusted-host retention only; not an approval API or source write.

        Analysis never calls this method. Test fixtures can exercise the future
        contracts; production adapters must supply observed source records.
        """
        actor.require_scope(record.origin.customer_id, record.origin.program_id)
        with self.transaction(write=True) as data:
            run = data.runs.get(record.origin.run_id)
            if not run or Origin.from_run(run) != record.origin or run.status != "completed":
                raise WorkflowError("RECORD_RUN_MISMATCH")
            proposal_id = record.proposal_id if not isinstance(record, VerificationRecord) else None
            action_id = record.action_id if isinstance(record, (ActionAttempt, VerificationRecord)) else None
            if isinstance(record, Proposal):
                record = validate_proposal(record)
                if record.source_plan.change_id != data.cases[run.case_id].change_id:
                    raise WorkflowError("PROPOSAL_SCOPE_MISMATCH")
                collection, key, kind = data.proposals, f"{record.proposal_id}:{record.proposal_version}", "proposal_retained"
                data.proposal_status.setdefault(key, "current")
            elif isinstance(record, (DecisionBinding, ActionAttempt)):
                proposal = data.proposals.get(f"{record.proposal_id}:{record.proposal_version}")
                if not proposal or proposal.origin != record.origin or proposal.proposal_digest != record.proposal_digest:
                    raise WorkflowError("RECORD_PROPOSAL_MISMATCH")
                if isinstance(record, DecisionBinding):
                    if record.source_decision.plan_id != proposal.source_plan.id or record.source_decision.plan_digest != proposal.source_plan.plan_digest:
                        raise WorkflowError("DECISION_SOURCE_MISMATCH")
                    collection, key, kind = data.decisions, record.source_decision.id, "source_decision_retained"
                else:
                    binding = data.decisions.get(record.decision_id)
                    if not binding or binding.proposal_digest != record.proposal_digest or binding.source_decision.decision != "approve":
                        raise WorkflowError("ACTION_DECISION_MISMATCH")
                    collection, key, kind = data.actions, record.action_id, "action_record_retained"
            elif isinstance(record, VerificationRecord):
                action = data.actions.get(record.action_id)
                if not action or action.origin != record.origin:
                    raise WorkflowError("VERIFICATION_ACTION_MISMATCH")
                claim = "job_scheduled" if action.action == "schedule_validation" else "planner_link_recorded"
                if record.claim != claim:
                    raise WorkflowError("VERIFICATION_CLAIM_MISMATCH")
                proposal_id = action.proposal_id
                collection, key, kind = data.verifications, record.verification_id, "verification_record_retained"
            else:
                raise WorkflowError("UNSUPPORTED_RECORD")
            if key in collection:
                if collection[key] != record:
                    raise WorkflowError("IMMUTABLE_RECORD_CONFLICT")
                return
            # Serialize/copy to prevent mutations of caller-owned nested objects.
            collection[key] = type(record).model_validate_json(record.model_dump_json())
            self._activity(data, run, kind, proposal_id=proposal_id, action_id=action_id,
                actor=actor, details={"record_id": key, "source": "trusted_host_input"})
