"""Parameter database exceptions."""


class ParamDataNotIntializedError(Exception):
    """Parameter data has not finished initializing."""


class NoParentError(Exception):
    """Parameter data has no parent."""


class CommitNotFoundError(Exception):
    """Commit does not exist in the database."""
