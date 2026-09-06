"""
@Author     : zarkhan
@CreateDate : 2026/9/6
@Description: 内置健康检查器
              - AppChecker：应用基本信息（状态、版本、运行时长）
              - DatabaseChecker：数据库连通性（基于 EngineManager）
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI
from sqlalchemy import text

from .checker import (
    BaseChecker,
    CheckResult,
    STATUS_HEALTHY,
    STATUS_UNHEALTHY,
)


class AppChecker(BaseChecker):
    """应用基本健康检查。

    返回应用运行状态、版本、运行时长。
    通过 ``app.state.start_time`` 获取启动时间戳（由工厂或用户设置）。
    """

    @property
    def name(self) -> str:
        return 'app'

    async def check(self, app: Any) -> CheckResult:
        """检查应用状态。

        Args:
            app: FastAPI 应用实例

        Returns:
            包含版本、状态、运行时长的检查结果
        """
        start_time = getattr(app.state, 'start_time', None)
        uptime = time.time() - start_time if start_time else 0.0

        return CheckResult(
            name=self.name,
            status=STATUS_HEALTHY,
            latency_ms=0.0,
            details={
                'status': 'running',
                'version': app.version if isinstance(app, FastAPI) else '',
                'uptime_seconds': round(uptime, 2),
            },
        )


class DatabaseChecker(BaseChecker):
    """数据库连通性健康检查。

    通过 ``app.state.engine_manager`` 获取写引擎，执行 ``SELECT 1`` 验证连通性。
    若未挂载 ``engine_manager``，则跳过检查并返回 ``unhealthy``。
    """

    def __init__(self, name: str = 'database') -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def check(self, app: Any) -> CheckResult:
        """检查数据库连通性。

        Args:
            app: FastAPI 应用实例

        Returns:
            数据库连通性检查结果
        """
        engine_manager = getattr(app.state, 'engine_manager', None)
        if engine_manager is None:
            return CheckResult(
                name=self.name,
                status=STATUS_UNHEALTHY,
                details={'error': 'engine_manager not found on app.state'},
            )

        start = time.perf_counter()
        try:
            engine = engine_manager.write_engine
            async with engine.connect() as conn:
                await conn.execute(text('SELECT 1'))
            latency = (time.perf_counter() - start) * 1000

            return CheckResult(
                name=self.name,
                status=STATUS_HEALTHY,
                latency_ms=round(latency, 2),
            )
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return CheckResult(
                name=self.name,
                status=STATUS_UNHEALTHY,
                latency_ms=round(latency, 2),
                details={'error': str(e)},
            )
