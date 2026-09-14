import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Request


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def new_id(prefix: str) -> str:
    return prefix + '-' + uuid4().hex


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace('Z', '+00:00'))


def iso(value: datetime) -> str:
    return value.isoformat().replace('+00:00', 'Z')


class BusinessError(Exception):
    def __init__(self, status: int, code: str, message: str, **details):
        self.status, self.code, self.message, self.details = status, code, message, details
        super().__init__(code)


def fail(condition: bool, status: int, code: str, message: str, **details):
    if not condition:
        raise BusinessError(status, code, message, **details)


# Explicit server-owned authorization map. Query parameters cannot add membership.
PORTFOLIO_SCOPES = (('PRG-A17','CUST-FML01'),) + tuple(zip(
    (f'PRG-P{i:02}' for i in range(1,11)),
    ('CUST-NORTH','CUST-VELA','CUST-MERIDIAN','CUST-QUANTA','CUST-ARCADIA','CUST-NOVA','CUST-ATLAS','CUST-HORIZON','CUST-VELA','CUST-ARCADIA'),
))


@dataclass(frozen=True)
class Identity:
    id: str
    role: str
    program_id: str = 'PRG-A17'
    customer_id: str = 'CUST-FML01'
    portfolio: bool = False

    @property
    def scopes(self):
        if self.portfolio:
            return PORTFOLIO_SCOPES
        return ((self.program_id, self.customer_id),)

    def scoped(self, program_id, customer_id):
        fail((program_id, customer_id) in self.scopes, 404, 'NOT_FOUND', 'Resource not found.')
        return replace(self, program_id=program_id, customer_id=customer_id, portfolio=False)


# Public demo role selectors, deliberately NOT production authentication secrets.
IDENTITIES = {f'demo-{role}-local-only': Identity(f'demo-{role}', role)
              for role in ('automation', 'engineer', 'reader')}
IDENTITIES.update({f'demo-portfolio-{role}-local-only': Identity(f'demo-portfolio-{role}', role, portfolio=True)
                   for role in ('automation', 'engineer', 'reader')})

IDENTITIES['demo-program-owner-local-only'] = Identity('demo-program-owner', 'program_owner')

# A separate source-only lab persona; never supplied to agents or control host.
IDENTITIES['demo-lab-local-only'] = Identity('demo-lab', 'lab')

def identity(request: Request) -> Identity:
    scheme, _, token = request.headers.get('authorization', '').partition(' ')
    actor = IDENTITIES.get(token) if scheme.lower() == 'bearer' else None
    request.state.actor = actor
    fail(actor is not None, 401, 'UNAUTHENTICATED', 'Known local demo identity required.')
    return actor


def role(request: Request, expected: str):
    actor = identity(request)
    fail(actor.role == expected, 403, 'FORBIDDEN_ROLE', 'Role is not authorized for this action.')
    return actor


def header_id(value: str | None) -> str:
    return value if value and re.fullmatch(r'[A-Za-z0-9_.:-]{1,100}', value) else new_id('corr')


def metadata(store, owner: str, record_id: str, actor: Identity) -> dict:
    return dict(id=record_id, content_version=1, owning_system=owner, synthetic=True,
                updated_at=store.now, program_id=actor.program_id)
