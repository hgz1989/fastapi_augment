"""
@Author         : hangu
@CreateDate     : 2026/8/31
@Description    : fastapi-augment — 生产级 FastAPI 应用框架
"""
from .factory import create_app
from .lifespan import (
    HookFunc,
    HookRegistry,
    core_registry,
    fastapi_lifespan,
    clear_hooks
)

__all__ = [
    # factory
    'create_app',
    # lifespan
    'HookFunc',
    'HookRegistry',
    'core_registry',
    'fastapi_lifespan',
    'clear_hooks',
]
