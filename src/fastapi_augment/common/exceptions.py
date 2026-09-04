"""
@Author         : hangu
@CreateDate     : 2026/9/4
@Description    : 统一业务异常
"""
from typing import Any

from starlette import status
from starlette.exceptions import HTTPException

from .constants import DEFAULT_ERR_MSG


# ===================== 通用基类：统一封装 detail + headers 逻辑 =====================
class BaseHttpError(HTTPException):
    """统一HTTP异常基类，所有4xx异常继承此类，原生兼容starlette.HTTPException.

    Attributes:
        status_code: HTTP状态码
        detail: 异常提示文案
        headers: 响应附加http头
    """
    __slots__ = ()

    def __init__(
            self,
            status_code: int,
            detail: str | None = None,
            headers: dict[str, Any] | None = None,
    ):
        """初始化http业务异常.

        Args:
            status_code: http响应状态码
            detail: 自定义错误提示，不传使用内置默认文案
            headers: 附加响应头

        Raises:
            KeyError: 传入未在DEFAULT_ERR_MSG定义的status_code
        """
        if status_code not in DEFAULT_ERR_MSG:
            raise KeyError(f'status_code {status_code} not defined in DEFAULT_ERR_MSG')
        msg = detail or DEFAULT_ERR_MSG[status_code]
        super().__init__(status_code=status_code, detail=msg, headers=headers)


# ===================== 各类4xx异常子类（极简声明，无重复__init__） =====================
class BadRequestError(BaseHttpError):
    """400 请求错误."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)


class UnauthorizedError(BaseHttpError):
    """401 未授权错误."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail=detail, headers=headers)


class PaymentRequiredError(BaseHttpError):
    """402 需要付费错误."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_402_PAYMENT_REQUIRED, detail=detail, headers=headers)


class ForbiddenError(BaseHttpError):
    """403 禁止访问错误."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)


class NotFoundError(BaseHttpError):
    """404 未找到资源."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)


class MethodNotAllowedError(BaseHttpError):
    """405 请求方法不允许."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_405_METHOD_NOT_ALLOWED, detail=detail, headers=headers)


class NotAcceptableError(BaseHttpError):
    """406 客户端不支持返回格式."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_406_NOT_ACCEPTABLE, detail=detail, headers=headers)


class RequestTimeoutError(BaseHttpError):
    """408 请求超时."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_408_REQUEST_TIMEOUT, detail=detail, headers=headers)


class ConflictError(BaseHttpError):
    """409 资源冲突."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_409_CONFLICT, detail=detail, headers=headers)


class GoneError(BaseHttpError):
    """410 资源已永久删除."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_410_GONE, detail=detail, headers=headers)


class PreconditionFailedError(BaseHttpError):
    """412 前置校验失败."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_412_PRECONDITION_FAILED, detail=detail, headers=headers)


class PayloadTooLargeError(BaseHttpError):
    """413 请求体过大."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_413_CONTENT_TOO_LARGE, detail=detail, headers=headers)


class URITooLongError(BaseHttpError):
    """414 URI链接过长."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_414_URI_TOO_LONG, detail=detail, headers=headers)


class UnsupportedMediaTypeError(BaseHttpError):
    """415 不支持的请求媒体类型."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=detail, headers=headers)


class LockedError(BaseHttpError):
    """423 资源锁定."""

    def __init__(self, detail: str | None = None, headers: dict[str, Any] | None = None):
        """

        Args:
            detail: 自定义错误提示
            headers: 附加响应头
        """
        super().__init__(status.HTTP_423_LOCKED, detail=detail, headers=headers)


class TooManyRequestsError(BaseHttpError):
    """429 请求过于频繁（限流专用，支持retry_after快捷参数）."""

    def __init__(
            self,
            detail: str | None = None,
            retry_after: int | None = None,
            headers: dict[str, Any] | None = None,
    ):
        """

        Args:
            detail: 自定义错误提示
            retry_after: 设置 Retry‑After 响应头，单位秒
            headers: 自定义附加响应头
        """
        final_headers: dict[str, Any] = dict(headers) if headers is not None else {}
        if retry_after is not None:
            final_headers['Retry-After'] = str(retry_after)
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=final_headers if final_headers else None
        )
