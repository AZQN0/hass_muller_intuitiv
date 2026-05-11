"""Custom exceptions for Muller Intuitiv integration."""


class MullerIntuitivError(Exception):
    """Base exception for Muller Intuitiv integration."""


class MullerIntuitivAuthError(MullerIntuitivError):
    """Exception for authentication errors."""


class MullerIntuitivApiError(MullerIntuitivError):
    """Exception for general API errors."""


class MullerIntuitivTimeoutError(MullerIntuitivApiError):
    """Exception for timeout errors."""


class MullerIntuitivConnectionError(MullerIntuitivApiError):
    """Exception for connection errors."""


class MullerIntuitivRateLimitError(MullerIntuitivApiError):
    """Exception for rate limit errors."""


class MullerIntuitivDeviceNotFoundError(MullerIntuitivError):
    """Exception for device not found errors."""