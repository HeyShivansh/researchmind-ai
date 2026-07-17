"""
Domain exceptions for the Paper entity.

All paper-related errors inherit from ``PaperError`` so that callers
can catch a single base type when appropriate.
"""


class PaperError(Exception):
    """
    Base exception for all Paper domain errors.

    All concrete paper exceptions should inherit from this class.
    """


class PaperNotFoundError(PaperError):
    """
    Raised when a requested paper does not exist.

    Parameters
    ----------
    paper_id : object
        The identifier that was used to look up the paper.
    """

    def __init__(self, paper_id: object) -> None:
        self.paper_id = paper_id
        super().__init__(f"Paper with id '{paper_id}' not found")


class DuplicatePaperError(PaperError):
    """
    Raised when an attempt is made to create a paper with a DOI that
    already exists in the database.

    Parameters
    ----------
    doi : str
        The conflicting Digital Object Identifier.
    """

    def __init__(self, doi: str) -> None:
        self.doi = doi
        super().__init__(f"Paper with DOI '{doi}' already exists")
