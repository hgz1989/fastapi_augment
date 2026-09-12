"""
@Author         : hangu
@CreateDate     : 2026/9/4
@Description    : 全局常量与统一默认错误文案
"""
from starlette import status

# ===================== 统一默认文案常量（便于统一修改/国际化） =====================
DEFAULT_ERR_MSG: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: 'Bad request',
    status.HTTP_401_UNAUTHORIZED: 'Unauthorized',
    status.HTTP_402_PAYMENT_REQUIRED: 'Payment required',
    status.HTTP_403_FORBIDDEN: 'Forbidden',
    status.HTTP_404_NOT_FOUND: 'Not found',
    status.HTTP_405_METHOD_NOT_ALLOWED: 'Method not allowed',
    status.HTTP_406_NOT_ACCEPTABLE: 'Not acceptable',
    status.HTTP_408_REQUEST_TIMEOUT: 'Request timeout',
    status.HTTP_409_CONFLICT: 'Conflict',
    status.HTTP_410_GONE: 'Gone',
    status.HTTP_412_PRECONDITION_FAILED: 'Precondition failed',
    status.HTTP_413_CONTENT_TOO_LARGE: 'Payload too large',
    status.HTTP_414_URI_TOO_LONG: 'URI too long',
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: 'Unsupported media type',
    status.HTTP_422_UNPROCESSABLE_CONTENT: 'Unprocessable entity',
    status.HTTP_423_LOCKED: 'Locked',
    status.HTTP_429_TOO_MANY_REQUESTS: 'Too many requests',
}
