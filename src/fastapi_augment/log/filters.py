"""
@Author     : zarkhan
@CreateDate : 2026/9/6
@Description: 日志过滤器，统一uvicorn日志名称
"""
import logging


class UvicornNameRewriteFilter(logging.Filter):
    """日志过滤器，统一uvicorn.error / uvicorn.access的名称为uvicorn"""

    def filter(self, record: logging.LogRecord) -> bool:
        """将uvicorn.error / uvicorn.access的日志名称统一重写为uvicorn

        Args:
            record: 当前日志记录对象

        Returns:
            始终返回True，确保日志记录正常输出
        """
        if record.name in ('uvicorn.error', 'uvicorn.access'):
            record.name = 'uvicorn'
        return True
