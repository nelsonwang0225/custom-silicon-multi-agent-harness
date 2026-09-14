"""The single supported Manufacturing event. It conveys provenance, not authority."""
from typing import Literal
from datetime import datetime
from pydantic import field_validator
from .standard_models import Strict, Digest
from .config import RecordID


class QualitySourceEvent(Strict):
    event_id: RecordID
    event_version: Literal[1] = 1
    event_name: Literal['quality_exception_created'] = 'quality_exception_created'
    exception_id: Literal['QE-011'] = 'QE-011'
    program_id: Literal['PRG-A17'] = 'PRG-A17'
    customer_id: Literal['CUST-FML01'] = 'CUST-FML01'
    lot_id: Literal['LOT-B-219'] = 'LOT-B-219'
    source_system: Literal['manufacturing'] = 'manufacturing'
    source_record_version: Literal[1] = 1
    source_record_updated_at: str
    context_digest: Digest
    event_timestamp: str
    synthetic: Literal[True] = True

    @field_validator('event_timestamp', 'source_record_updated_at')
    @classmethod
    def utc_timestamp(cls, value):
        if not value.endswith('Z'): raise ValueError('Explicit UTC timestamp required')
        datetime.fromisoformat(value.replace('Z','+00:00'))
        return value
