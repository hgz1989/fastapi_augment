"""
@Author     : zarkhan
@CreateDate : 2026/9/6
@Description: 基于 pydantic-settings 的环境配置管理
              - 支持 .env 文件加载（路径由使用者显式指定）
              - 支持环境变量前缀
              - 支持嵌套配置（通过分隔符）
"""
from __future__ import annotations

from typing import Any, TypeVar

from pydantic_settings import BaseSettings, SettingsConfigDict

# SettingsConfigDict 所有可用键，用于区分配置参数和模型字段值
_CONFIG_KEYS = frozenset(SettingsConfigDict.__annotations__.keys())

_S = TypeVar('_S', bound='EnvSettings')


class EnvSettings(BaseSettings):
    """环境配置基类，继承 pydantic_settings.BaseSettings。

    自动从环境变量和 ``.env`` 文件加载配置，通过 ``from_env()`` 直接传参::

        from fastapi_augment.config import EnvSettings

        class Settings(EnvSettings):
            database_url: str
            redis_url: str = ''
            debug: bool = False

        # 直接传入 .env 路径、前缀等，无需导入 SettingsConfigDict
        settings = Settings.from_env(
            env_file='config/.env',
            env_prefix='APP_',
        )

    特性：
        - ``.env`` 文件路径由使用者显式指定，库不猜测项目根目录
        - 支持 ``env_prefix`` 前缀过滤（如 ``APP_`` → ``APP_DATABASE_URL``）
        - 支持 ``env_nested_delimiter`` 嵌套配置（如 ``DB__URL=xxx``）
        - 环境变量优先级高于 .env 文件
        - 默认 ``extra='ignore'``，未声明的环境变量被安全忽略
    """

    model_config = SettingsConfigDict(
        env_prefix='',
        env_file=None,
        env_nested_delimiter=None,
        case_sensitive=False,
        extra='ignore',
    )

    # ------------------------------
    # 项目信息
    # ------------------------------
    project_debug: bool = True
    project_title: str = 'FastAPI Augment'
    project_summary: str = 'FastAPI Augment - Extended utilities and patterns for FastAPI'
    project_description: str = (
        'FastAPI Augment is a lightweight extension library for FastAPI that '
        'provides out-of-the-box solutions for common backend challenges. It '
        'includes asynchronous database session management (with read-write splitting), '
        'unified API response models, pagination helpers, and streamlined dependency '
        'injection for transactional operations. Designed to reduce boilerplate and '
        'enforce clean architecture, it accelerates the development of production-ready '
        'web services.'
    )
    project_version: str = '0.1.0'

    @classmethod
    def from_env(cls: type[_S], **kwargs: Any) -> _S:
        """从环境加载配置，支持 ``SettingsConfigDict`` 所有参数。

        内部自动区分 ``SettingsConfigDict`` 配置参数和模型字段值：
        - 属于 ``SettingsConfigDict`` 的键 → 覆盖 ``model_config``
        - 其余键 → 直接覆盖模型字段值（优先级最高）

        常用配置参数：
            env_file: .env 文件路径
            env_prefix: 环境变量前缀（如 ``'APP_'``）
            env_nested_delimiter: 嵌套配置分隔符（如 ``'__'``）
            case_sensitive: 环境变量大小写敏感
            env_file_encoding: .env 文件编码
            secrets_dir: secrets 目录路径
            json_file: JSON 配置文件路径
            yaml_file: YAML 配置文件路径
            toml_file: TOML 配置文件路径
            cli_parse_args: 是否解析命令行参数

        Returns:
            配置实例

        Example::

            settings = Settings.from_env(
                env_file='config/.env',
                env_prefix='APP_',
                env_nested_delimiter='__',
                debug=True,               # 模型字段值覆盖
            )
        """
        config_overrides: dict[str, Any] = {}
        field_overrides: dict[str, Any] = {}

        for key, value in kwargs.items():
            if key in _CONFIG_KEYS:
                config_overrides[key] = str(value) if key == 'env_file' and value is not None else value
            else:
                field_overrides[key] = value

        if config_overrides:
            sub_cls = type(
                f'{cls.__name__}__env',
                (cls,),
                {'model_config': SettingsConfigDict(**{**dict(cls.model_config), **config_overrides})},
            )
            return sub_cls(**field_overrides)

        return cls(**field_overrides)
