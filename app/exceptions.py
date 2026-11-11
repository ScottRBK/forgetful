"""Domain exceptions for the application
"""

class NotFoundError(Exception):
    """Raised when a requested resource is not found"""

class BundleReadDeniedError(Exception):
    """Resource kinds excluded from an export; contains no stored values."""

    def __init__(self, kinds: set[str]):
        self.kinds = frozenset(kinds)
        super().__init__("Bundle resource read is not permitted")


class ConflictError(Exception):
    """Raised when there's a resource conflict (e.g., duplicate key)"""


class InvalidStateTransitionError(Exception):
    """Raised when a state machine transition is not allowed"""


class DependencyNotMetError(Exception):
    """Raised when task dependencies are not satisfied for a transition"""


class CyclicDependencyError(Exception):
    """Raised when adding a dependency would create a cycle"""


class WritePluginRejectedError(Exception):
    """A Write Plugin rejected the pending memory write with a client-safe message."""


class WritePluginUnavailableError(Exception):
    """A configured Write Plugin could not decide whether a write may proceed."""


class PlanPluginRejectedError(Exception):
    """A Plan Plugin rejected a pending plan mutation with a client-safe message."""


class PlanPluginUnavailableError(Exception):
    """A configured Plan Plugin could not decide whether a mutation may proceed."""


class PlanPluginStateChangedError(Exception):
    """Plan state changed while a registered before handler was awaited."""
