"""Domain exceptions for the application
"""

class NotFoundError(Exception):
    """Raised when a requested resource is not found"""

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
