"""Errors raised by embedders."""


class EmbeddingBackendError(RuntimeError):
    """A backend could not produce trustworthy vectors."""
