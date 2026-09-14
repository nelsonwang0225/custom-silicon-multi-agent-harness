"""Read-only HTTP access to Stratos Silicon; independent of the mock backend."""

from .client import EnterpriseClient
from .config import ClientConfig, Scope
from .errors import EnterpriseAPIError

__all__ = ["EnterpriseClient", "ClientConfig", "Scope", "EnterpriseAPIError"]
