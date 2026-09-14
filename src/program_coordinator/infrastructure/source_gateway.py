"""Host-only typed HTTP mutations; existing EnterpriseClient stays GET-only.

No gateway is registered with an agent/MCP server. Demo identities are fixed host
contexts matching the source server's map, not user/model supplied roles.
"""
from dataclasses import dataclass
import re

import httpx
from enterprise_api.client import EnterpriseClient
from enterprise_api.config import ClientConfig, Scope
from enterprise_api.transport import HttpxReadTransport
from mock_enterprise.schemas import PlanInput, DecisionInput, JobInput, LinkInput, PlanView, Decision, JobView, LinkView
from ..application.models import WorkflowError
from ..application.execution_models import SourceFailure, SourceReadFailure
from ..application.demo_identity import AUTOMATION, ENGINEER, READER, PROGRAM_OWNER
from enterprise_api.errors import EnterpriseAPIError

@dataclass(frozen=True)
class Receipt:
    body: dict
    request_id: str | None
    replayed: bool = False


class SourceGateway:
    def __init__(self, base_url='http://127.0.0.1:8000', *, demo_mode=False, http_client=None):
        if not demo_mode:
            raise WorkflowError('DEMO_MODE_REQUIRED')
        self.config = ClientConfig(base_url=base_url, scope=Scope(customer_id='CUST-FML01', program_id='PRG-A17'), max_retries=0)
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(trust_env=False, follow_redirects=False, timeout=10)
        self.read = ReadGateway(EnterpriseClient(self.config, transport=HttpxReadTransport(self.config, http_client=self._http)))

    def close(self):
        self.read.close()
        if self._owns_http:
            self._http.close()

    def _post(self, path, body, key, response_type, *, selector='demo-automation-local-only'):
        # Only private callers below define routes/selectors. Never retry a write
        # here; the execution service first reconciles any uncertain outcome.
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', key):
            raise WorkflowError('INVALID_IDEMPOTENCY_KEY')
        try:
            response = self._http.post(self.config.base_url + '/api/v1' + path,
                headers={'Authorization': 'Bearer ' + selector, 'Idempotency-Key': key,
                         'X-Correlation-ID': key}, json=body.model_dump(mode='json'), follow_redirects=False)
        except httpx.HTTPError:
            raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True) from None
        if not 200 <= response.status_code < 300:
            # Server/proxy errors may occur after a commit. Never assume rollback.
            if response.status_code >= 500:
                raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True)
            try:
                code = response.json()['error']['code']
            except (ValueError, KeyError, TypeError):
                code = 'SOURCE_WRITE_REJECTED'
            known = {'STALE_SOURCE', 'STALE_MILESTONE', 'RESOURCE_CONFLICT', 'RESOURCE_INELIGIBLE',
                     'FORBIDDEN_ROLE', 'APPROVAL_REQUIRED', 'APPROVAL_POLICY_EXCEEDED',
                     'ACTION_ALREADY_RECORDED', 'IDEMPOTENCY_CONFLICT', 'NOT_FOUND', 'INVALID_SOURCE_SET',
                     'DELIVERY_NOT_READY', 'COMMITMENT_ALREADY_CURRENT', 'COMMITMENT_REQUIRED', 'VERIFICATION_MISMATCH', 'QUALITY_POLICY_INELIGIBLE', 'INVESTIGATION_REQUIRED', 'STALE_PLAN', 'DECISION_CONFLICT', 'STANDARD_POLICY_INELIGIBLE', 'INVALID_HANDOFF_PACKAGE', 'STANDARD_UPGRADE_REQUIRED'}
            raise SourceFailure(code if code in known else 'SOURCE_WRITE_REJECTED')
        try:
            parsed = response_type.model_validate(response.json()).model_dump(mode='json')
        except (ValueError, TypeError):
            raise SourceFailure('SOURCE_OUTCOME_UNKNOWN', unknown=True) from None
        request_id = response.headers.get('x-request-id', '')
        return Receipt(parsed, request_id if re.fullmatch(r'request-[a-f0-9]{32}', request_id) else None,
                       response.headers.get('idempotency-replayed') == 'true')

    def create_plan(self, body: PlanInput, key: str):
        return self._post('/engineering/changes/CR-017/plans', PlanInput.model_validate(body), key, PlanView)

    def standard_intake(self, body, key: str):
        from enterprise_api.standard_models import StandardIntakeInput, ValidationIntake
        value = StandardIntakeInput.model_validate(body)
        return self._post('/validation/changes/' + value.package.change_id + '/intakes', value, key, ValidationIntake)

    def delivery_prepare(self, body, key):
        from enterprise_api.delivery_models import DeliveryPrepareInput, CommitmentPlan
        return self._post('/erp/commitment-plans', DeliveryPrepareInput.model_validate(body), key, CommitmentPlan)

    def delivery_commit(self, body, key):
        from enterprise_api.delivery_models import DeliveryExecuteInput, DeliveryCommitment
        return self._post('/erp/delivery-commitments', DeliveryExecuteInput.model_validate(body), key, DeliveryCommitment)

    def delivery_link(self, body, key):
        from enterprise_api.delivery_models import DeliveryExecuteInput, DeliveryLink
        return self._post('/programs/delivery-links', DeliveryExecuteInput.model_validate(body), key, DeliveryLink)

    def quality_investigate(self, body, key):
        from enterprise_api.quality_models import QualityIntent, QualityInvestigation
        return self._post('/manufacturing/quality-investigations', QualityIntent.model_validate(body), key, QualityInvestigation)

    def quality_prepare(self, body, key):
        from enterprise_api.quality_models import QualityIntent, RecoveryPlan
        return self._post('/manufacturing/recovery-plans', QualityIntent.model_validate(body), key, RecoveryPlan)

    def quality_execute(self, body, key):
        from enterprise_api.quality_models import RecoveryExecuteInput, RecoveryTask
        return self._post('/programs/recovery-tasks', RecoveryExecuteInput.model_validate(body), key, RecoveryTask)

    def schedule(self, body: JobInput, key: str):
        return self._post('/validation/jobs', JobInput.model_validate(body), key, JobView)

    def link(self, body: LinkInput, key: str):
        return self._post('/programs/PRG-A17/implementation-links', LinkInput.model_validate(body), key, LinkView)


class HumanDecisionGateway(SourceGateway):
    """Only the trusted review host constructs this capability, never the agents."""
    def delivery_decide(self, body, key, actor):
        from enterprise_api.quality_models import RecoveryReviewInput
        from enterprise_api.delivery_models import CommitmentDecision
        if actor is not PROGRAM_OWNER: raise WorkflowError('WRONG_APPROVER')
        return self._post('/erp/commitment-decisions', RecoveryReviewInput.model_validate(body), key, CommitmentDecision, selector='demo-program-owner-local-only')

    def quality_decide(self, body, key, actor):
        from enterprise_api.quality_models import RecoveryReviewInput, RecoveryDecision
        if actor is not PROGRAM_OWNER: raise WorkflowError('WRONG_APPROVER')
        return self._post('/manufacturing/recovery-decisions', RecoveryReviewInput.model_validate(body), key, RecoveryDecision,
            selector='demo-program-owner-local-only')

    def decide(self, plan_id, body: DecisionInput, key: str, actor):
        if actor is not ENGINEER:
            raise WorkflowError('WRONG_APPROVER')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', plan_id):
            raise WorkflowError('INVALID_PLAN_ID')
        return self._post('/engineering/plans/' + plan_id + '/decisions', DecisionInput.model_validate(body), key,
                          Decision, selector='demo-engineer-local-only')


class ReadGateway:
    """Normalize existing typed client failures at the application boundary."""
    def __init__(self, client):
        self._client = client

    def __getattr__(self, name):
        if not name.startswith('get_'):
            raise AttributeError(name)
        method = getattr(self._client, name)
        def read(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except EnterpriseAPIError:
                raise SourceReadFailure('SOURCE_READ_FAILED') from None
        return read

    def close(self):
        self._client.close()
