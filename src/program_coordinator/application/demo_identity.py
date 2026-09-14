"""Host-installed public role-test contexts aligned with the source identity map.

The trusted CLI review command installs ENGINEER. No serialized role or model
output can construct an accepted context. These are not real authentication.
"""
from .models import TrustedActor

SCOPE = frozenset({('CUST-FML01', 'PRG-A17')})
READER = TrustedActor('demo-reader', 'reader', SCOPE)
AUTOMATION = TrustedActor('demo-automation', 'automation', SCOPE)
ENGINEER = TrustedActor('demo-engineer', 'engineer', SCOPE)

PROGRAM_OWNER = TrustedActor('demo-program-owner', 'program_owner', SCOPE)
