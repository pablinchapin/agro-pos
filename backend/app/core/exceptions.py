class DomainError(Exception):
    """Base class for all business rule violations."""
    pass


class NotFoundError(DomainError):
    pass


class DuplicateError(DomainError):
    pass


class InsufficientStockError(DomainError):
    pass


class AuthenticationError(DomainError):
    """Raised when login credentials are invalid or the account is inactive."""
    pass
