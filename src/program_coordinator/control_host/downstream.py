"""Thin downstream orchestration over source HTTP and the unchanged CaseHarness."""
from typing import Literal
import httpx
from pydantic import Field
from mock_enterprise.downstream_models import PhysicalValidation, EvidenceReviewInput, EvidenceReview
from ..models import Model, ValidationEvidenceAssessment
from ..application.models import WorkflowError
from ..application.demo_identity import ENGINEER
from ..application.execution_models import SourceReadFailure, SourceFailure


class EvidenceRequest(Model):
    expected_evidence_digest: str = Field(pattern=r'^[a-f0-9]{64}$')


class AssessRequest(EvidenceRequest):
    retry_run_id: str | None = Field(default=None, pattern=r'^run_[a-f0-9]{32}$')


class ReviewEvidenceRequest(EvidenceRequest):
    decision: Literal['approve', 'reject']
    comment: str = Field(min_length=1, max_length=1500)


class AssessmentView(Model):
    run_id: str
    evidence_digest: str
    confirmed: bool
    summary: str


class DownstreamView(Model):
    physical: PhysicalValidation
    assessment: AssessmentView | None = None
    review_ready: bool = False


def read_physical(source):
    try:
        response = source._http.get(source.config.base_url + '/api/v1/validation/changes/CR-017/physical-validation',
            headers={'Authorization': 'Bearer demo-reader-local-only'}, follow_redirects=False)
        if response.status_code == 404:
            return PhysicalValidation(available=False)
        response.raise_for_status()
        return PhysicalValidation.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        raise SourceReadFailure('SOURCE_READ_FAILED') from None


def view(host, physical=None):
    physical = physical or read_physical(host.source)
    with host.store.transaction() as data:
        records = [a for a in data.activity if a.details.get('operation') == 'assess_validation_result'
                   and a.details.get('evidence_digest') == physical.evidence_digest
                   and data.runs.get(a.run_id) and data.runs[a.run_id].status == 'completed']
    latest = records[-1] if records else None
    assessment = AssessmentView(run_id=latest.run_id, evidence_digest=physical.evidence_digest,
        confirmed=latest.details['confirmed'], summary=latest.details['summary']) if latest else None
    return DownstreamView(physical=physical, assessment=assessment,
        review_ready=physical.applicability == 'confirmed' and bool(assessment and assessment.confirmed))


def record_assessment(host, run, state, expected):
    physical = read_physical(host.source)
    assessments = [a.assessment for a in state.completed_assessments if isinstance(a.assessment, ValidationEvidenceAssessment)]
    confirmed = (physical.evidence_digest == expected and physical.applicability == 'confirmed'
        and state.final_package is not None and not state.final_package.evidence_gaps
        and state.final_package.policy_path == 'human_review_required'
        and not state.unresolved_questions and not state.blocking_issues
        and bool(assessments) and all(a.coverage_status == 'sufficient' and not a.evidence_gaps
            and any(e.result_id == physical.result.id and e.satisfies for e in a.applicable_evidence) for a in assessments))
    summary = ('Applicable validation evidence received for the exact CR-017 workload and configuration. The previous evidence gap is closed; engineering review is ready. Customer acceptance remains pending.' if confirmed else
        'Evidence gap remains or the result changed during reassessment. Engineering approval is not ready; inspect source mismatches and specialist findings.')
    with host.store.transaction(write=True) as data:
        if not any(a.run_id == run.run_id and a.details.get('operation') == 'assess_validation_result' for a in data.activity):
            host.store._activity(data, run, 'recommendation_recorded', details=dict(operation='assess_validation_result',
                evidence_digest=expected, confirmed=bool(confirmed), summary=summary))


def review_evidence(host, request, actor):
    if actor is not ENGINEER:
        with host.store.transaction(write=True) as data:
            runs = [r for r in data.runs.values() if r.program_id == 'PRG-A17' and r.customer_id == 'CUST-FML01']
            if runs:
                host.store._activity(data, runs[-1], 'execution_denied', actor=actor,
                    details={'operation': 'engineering_evidence_review', 'error_code': 'WRONG_APPROVER'})
        raise WorkflowError('WRONG_APPROVER')
    actor.require_scope('CUST-FML01', 'PRG-A17')
    current = view(host)
    if current.physical.evidence_digest != request.expected_evidence_digest:
        raise WorkflowError('STALE_EVIDENCE')
    existing = current.physical.current_review
    if existing:
        if existing.decision != request.decision or existing.reason != request.comment:
            raise WorkflowError('DECISION_CONFLICT')
        return existing
    if not current.review_ready:
        raise WorkflowError('EVIDENCE_REASSESSMENT_REQUIRED')
    body = EvidenceReviewInput(expected_evidence_digest=request.expected_evidence_digest,
        decision=request.decision, reason=request.comment)
    # One immutable source decision per exact evidence digest. A lost reply is recovered by source GET.
    key = 'ui_evidence_review_' + request.expected_evidence_digest
    receipt = host.human._post('/engineering/changes/CR-017/evidence-reviews', body, key, EvidenceReview,
        selector='demo-engineer-local-only')
    verified = read_physical(host.source).current_review
    if not verified or verified.model_dump(mode='json') != receipt.body:
        raise SourceFailure('EVIDENCE_REVIEW_READBACK_MISMATCH', unknown=True)
    return verified
