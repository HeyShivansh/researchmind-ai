"""Domain exceptions for the chunking subsystem."""


class ChunkingError(Exception):
    """
    Raised when chunking configuration or execution fails.

    Parameters
    ----------
    message : str
        Description of the chunking failure.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
