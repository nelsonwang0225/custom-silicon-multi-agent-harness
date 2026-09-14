"""Provider-independent discovery data. Text is untrusted evidence, never authority."""
from typing import Literal
from pydantic import Field
from ..models import Model

Profile = Literal['CHANGE_IMPACT', 'VALIDATION_EVIDENCE', 'MANUFACTURING_QUALITY', 'PROGRAM_COMMERCIAL', 'COORDINATOR']
PROFILES = {
    'CHANGE_IMPACT': {'policy','standard_routing_policy','requirement','engineering_specification','configuration','change_control_policy','architecture_note','design_note','playbook','customer_request'},
    'VALIDATION_EVIDENCE': {'policy','procedure','validation_procedure','acceptance_criteria','validation_report','test_report','qualification_guidance','requirement'},
    'MANUFACTURING_QUALITY': {'quality_sop','manufacturing_procedure','yield_investigation','historical_investigation','test_report','quality_report','errata'},
    'PROGRAM_COMMERCIAL': {'program_policy','customer_request','customer_requirement','planning_guidance','commitment_guidance','program_governance','policy','standard_routing_policy'},
    'COORDINATOR': set(),
}

class Metadata(Model):
    document_id: str
    title: str
    title_origin: str = 'source heading'
    document_type: str
    document_version: str
    program_id: str
    customer_id: str
    product: str | None = None
    configuration_id: str | None = None
    owner_team: str | None = None
    approval_status: str
    effective_date: str | None = None
    superseded_by: str | None = None
    source_system: str
    applicable_workflows: list[str] | None = None
    content_version: int
    record_version: int | None = None
    content_hash: str
    updated_at: str
    access_roles: list[str] | None = None
    historical: bool = False

class KnowledgeDocument(Model):
    metadata: Metadata
    content: str = Field(max_length=500000)

class Chunk(Model):
    chunk_id: str
    metadata: Metadata
    section: str | None
    page: int | None = None
    passage: str
    ordinal: int

class Filters(Model):
    document_ids: list[str] = Field(default_factory=list, max_length=30)
    document_types: list[str] = Field(default_factory=list, max_length=20)
    document_version: str | None = None
    configuration_id: str | None = None
    product: str | None = None
    include_historical: bool = False
    include_prior_versions: bool = False

class SearchRequest(Model):
    query: str = Field(min_length=2, max_length=1000)
    retrieval_profile: Profile
    program_id: str = 'PRG-A17'
    customer_id: str = 'CUST-FML01'
    metadata_filters: Filters = Field(default_factory=Filters)
    max_results: int = Field(default=6, ge=1, le=20)

class KnowledgeSourceReference(Model):
    document_id: str
    document_version: str
    content_version: int
    content_hash: str
    path: str
    verification_path: str

class KnowledgeResult(Model):
    document_id: str
    document_version: str
    chunk_id: str
    title: str
    section: str | None
    passage: str
    metadata: Metadata
    source_reference: KnowledgeSourceReference
    score: float | None
    rank: int
    current: bool
    flags: list[str]
    content_trust: Literal['untrusted_evidence'] = 'untrusted_evidence'

class SearchResponse(Model):
    query_id: str
    provider: str
    results: list[KnowledgeResult]
    result_count: int
    latency_ms: float
    index_state: str
    notice: str = 'Discovery only. Verify the exact source version. Current structured facts and host policy retain authority.'

class IndexDocument(Model):
    metadata: Metadata
    indexed: bool
    current: bool
    superseded: bool
    chunk_count: int

class IndexStatus(Model):
    provider: str
    state: str
    corpus_digest: str
    indexed_digest: str | None
    documents: list[IndexDocument]
    updated_at: str | None
    can_reindex: bool = False

class SyncRequest(Model):
    confirm: Literal['REINDEX KNOWLEDGE']
    rebuild: bool = False

class Verification(Model):
    verified: bool
    status: str
    document: KnowledgeDocument | None
    reference: KnowledgeSourceReference

class KnowledgePassageUse(Model):
    document_id: str
    document_version: str
    chunk_id: str
    section: str | None
    title: str
    metadata: Metadata
    current: bool
    score: float | None = None
    verification_state: str = 'not_verified'
    verification_id: str | None = None
    used_in_finding: bool = False

class KnowledgeEvent(Model):
    event_id: str
    at: str
    actor_id: str
    specialist: str
    profile: Profile
    run_id: str | None = None
    case_id: str | None = None
    invocation_id: str | None = None
    session_id: str | None = None
    query_id: str | None = None
    query: str
    why_relevant: str
    provider: str
    latency_ms: float = 0
    status: str
    passages: list[KnowledgePassageUse] = Field(default_factory=list)
