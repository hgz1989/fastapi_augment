"""
@Author         : hangu
@CreateDate     : 2026/9/4
@Description    : 通用模块 — 异常 / 异常处理器 / 常量
"""
from .constants import DEFAULT_ERR_MSG
from .exceptions import (
    BaseHttpError,
    BadRequestError,
    UnauthorizedError,
    PaymentRequiredError,
    ForbiddenError,
    NotFoundError,
    MethodNotAllowedError,
    NotAcceptableError,
    RequestTimeoutError,
    ConflictError,
    GoneError,
    PreconditionFailedError,
    PayloadTooLargeError,
    URITooLongError,
    UnsupportedMediaTypeError,
    LockedError,
    TooManyRequestsError
)
from .exception_handlers import (
    base_http_error_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
    register_exception_handlers
)

__all__ = [
    # constants
    'DEFAULT_ERR_MSG',
    # exceptions
    'BaseHttpError',
    'BadRequestError',
    'UnauthorizedError',
    'PaymentRequiredError',
    'ForbiddenError',
    'NotFoundError',
    'MethodNotAllowedError',
    'NotAcceptableError',
    'RequestTimeoutError',
    'ConflictError',
    'GoneError',
    'PreconditionFailedError',
    'PayloadTooLargeError',
    'URITooLongError',
    'UnsupportedMediaTypeError',
    'LockedError',
    'TooManyRequestsError',
    # exception handlers
    'base_http_error_handler',
    'http_exception_handler',
    'validation_exception_handler',
    'general_exception_handler',
    'register_exception_handlers'
]
