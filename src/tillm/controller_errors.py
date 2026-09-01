"""TILLM shell-drive error types."""


class TillmError(RuntimeError):
    """Base error for TILLM control failures."""


class UnknownClientError(TillmError):
    """Requested client is not registered."""


class ClientUnavailableError(TillmError):
    """Registered client command is not available in PATH."""


class ClientNotReadyError(TillmError):
    """Registered client is missing binary, env vars, or requested capability."""


class UnknownProfileError(TillmError):
    """Requested execute profile is not registered for the client."""
