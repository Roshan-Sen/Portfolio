"""Application-level exceptions shared by every user interface."""


class ExpenseTrackingError(Exception):
    """Base class for expected expense-tracking application failures."""


class ValidationError(ExpenseTrackingError, ValueError):
    """Raised when application input violates a domain rule."""


class TransactionError(ExpenseTrackingError):
    """Raised when a transaction cannot be stored."""


class QueryLoadError(TransactionError):
    """Raised when a transaction query cannot be loaded."""


class DatabaseError(TransactionError):
    """Raised when PostgreSQL rejects or cannot complete an operation."""


class ReportGenerationError(ExpenseTrackingError):
    """Raised when a cash-flow report cannot be generated."""
