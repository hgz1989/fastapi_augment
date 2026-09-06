"""
@Author     : zarkhan
@CreateDate : 2026/9/6
@Description: 多进程安全的日志轮转处理器，支持秒/分/时/天/周及自定义月/年轮转
"""
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler


class MultiProcessTimedRotatingFileHandler(TimedRotatingFileHandler):
    """支持多进程安全的按时间轮转处理器"""

    def doRollover(self) -> None:
        """执行轮转，捕获PermissionError以兼容多进程场景"""
        try:
            super().doRollover()
        except PermissionError:
            # 没抢到锁，说明其他进程正在轮转，重新打开新的文件流即可
            if self.stream:
                self.stream.close()
                self.stream = None
            self.stream = self._open()


class MonthlyRotatingFileHandler(MultiProcessTimedRotatingFileHandler):
    """按月轮转的日志处理器，以每月1日00:00:00为节点"""

    def __init__(self, filename: str, backup_count: int = 12, encoding: str = 'utf-8'):
        """初始化按月轮转处理器

        Args:
            filename: 日志文件路径
            backup_count: 保留的日志文件数量
            encoding: 文件编码
        """
        super().__init__(filename, when='midnight', backupCount=backup_count, encoding=encoding)

    def computeRollover(self, current_time: float) -> float:
        """计算下次轮转时间（下月1日00:00:00）

        Args:
            current_time: 当前UNIX时间戳

        Returns:
            下次轮转的UNIX时间戳
        """
        dt = datetime.fromtimestamp(current_time)

        if dt.month == 12:
            next_month = datetime(dt.year + 1, 1, 1)
        else:
            next_month = datetime(dt.year, dt.month + 1, 1)

        return next_month.timestamp()


class YearlyRotatingFileHandler(MultiProcessTimedRotatingFileHandler):
    """按年轮转的日志处理器，以每年1月1日00:00:00为节点"""

    def __init__(self, filename: str, backup_count: int = 5, encoding: str = 'utf-8'):
        """初始化按年轮转处理器

        Args:
            filename: 日志文件路径
            backup_count: 保留的日志文件数量
            encoding: 文件编码
        """
        super().__init__(filename, when='midnight', backupCount=backup_count, encoding=encoding)

    def computeRollover(self, current_time: float) -> float:
        """计算下次轮转时间（下一年1月1日00:00:00）

        Args:
            current_time: 当前UNIX时间戳

        Returns:
            下次轮转的UNIX时间戳
        """
        dt = datetime.fromtimestamp(current_time)
        next_year = datetime(dt.year + 1, 1, 1)
        return next_year.timestamp()
