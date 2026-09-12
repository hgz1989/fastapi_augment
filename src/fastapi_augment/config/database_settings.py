"""
@Author         : hangu
@CreateDate     : 2026/9/12
@Description    : 数据库配置——独立的嵌套 BaseModel，支持多数据库、自动推导驱动/端口
"""
from functools import cached_property
from typing import ClassVar, Self
from urllib.parse import parse_qsl

from pydantic import BaseModel, ConfigDict, model_validator

try:
    from sqlalchemy import URL

    _HAS_SQLALCHEMY = True
except ImportError:
    URL = None
    _HAS_SQLALCHEMY = False


class DatabaseSettings(BaseModel):
    """数据库配置，可通过 IAM_DATABASE__ 前缀的环境变量覆盖

    Example:
        .env 中写 ``IAM_DATABASE__HOST=192.168.1.100`` 即可覆盖 host
        .env 中写 ``IAM_DATABASE__ENGINE=mysql`` 即自动切换驱动和端口
    """
    model_config = ConfigDict(extra='ignore')

    # ------------------------------
    # 类级别常量
    # ------------------------------
    # 使用文件路径而非 host/port 的数据库引擎
    _FILE_BASED: ClassVar[frozenset[str]] = frozenset({'sqlite'})
    # 需要手动 refresh 刷新默认值的数据库引擎
    _REQUIRES_REFRESH: ClassVar[frozenset[str]] = frozenset({'mysql', 'sqlite', 'dm'})
    # 各引擎的默认异步驱动
    _DEFAULT_DRIVERS: ClassVar[dict[str, str]] = {
        'postgresql': 'asyncpg',
        'mysql': 'aiomysql',
        'sqlite': 'aiosqlite',
        'dm': 'dmAsync',
        'oracle': 'oracledb',
        'mssql': 'aioodbc',
    }
    # 各引擎的同步驱动（供 Alembic 等工具使用）
    _SYNC_DRIVERS: ClassVar[dict[str, str]] = {
        'postgresql': 'psycopg2',
        'mysql': 'pymysql',
        'sqlite': 'pysqlite',
        'dm': 'dmPython',
        'oracle': 'oracledb',
        'mssql': 'pyodbc',
    }
    # 各引擎的默认端口
    _DEFAULT_PORTS: ClassVar[dict[str, int]] = {
        'postgresql': 5432,
        'mysql': 3306,
        'dm': 5236,
        'oracle': 1521,
        'mssql': 1433,
    }
    # 各引擎在 URL query 中表示 SSL 模式的参数名
    _SSL_MODE_KEYS: ClassVar[dict[str, str]] = {
        'postgresql': 'sslmode',
        'mysql': 'ssl_mode',
        'dm': 'ssl_mode',
    }

    # ------------------------------
    # 公共配置
    # ------------------------------
    engine: str = 'postgresql'
    host: str = '127.0.0.1'
    port: int = 5432  # 0 表示按 engine 自动推导
    user: str = 'postgres'
    password: str = '<password>'
    name: str = '<name>'
    # SQLite 专用：文件路径，为空时回退到 name
    file_path: str = ''
    # 连接标识，便于 DBA 在 pg_stat_activity 等视图中定位来源
    application_name: str = 'iam'

    # ------------------------------
    # SQLAlchemy 专属配置
    # ------------------------------
    driver: str = ''  # 空表示按 engine 自动推导
    extra_query: str = ''
    echo: bool = False

    # 连接池
    pool_enabled: bool = True
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True
    pool_recycle: int = 3600
    pool_timeout: int = 30

    # 超时
    connect_timeout: int = 10
    command_timeout: int = 30

    # ------------------------------
    # SSL（按需启用）
    # ------------------------------
    ssl_mode: str = ''  # disable / require / verify-ca / verify-full
    ssl_ca: str = ''
    ssl_cert: str = ''
    ssl_key: str = ''

    # ------------------------------
    # 校验与默认值推导
    # ------------------------------
    @model_validator(mode='after')
    def _fill_defaults(self) -> Self:
        """根据 engine 推导 driver 和 port 的默认值"""
        engine = self.engine.lower()

        if not self.driver:
            self.driver = self._DEFAULT_DRIVERS.get(engine, '')

        if not self.port and engine not in self._FILE_BASED:
            self.port = self._DEFAULT_PORTS.get(engine, 0)

        return self

    # ------------------------------
    # 派生属性
    # ------------------------------
    @property
    def is_file_based(self) -> bool:
        """是否为文件型数据库（如 SQLite）"""
        return self.engine.lower() in self._FILE_BASED

    @property
    def requires_refresh(self) -> bool:
        """判断当前数据库引擎在新增/更新后是否需要手动 refresh 刷新默认值

        Returns:
            是否需要手动 refresh 刷新默认值
        """
        return self.engine.lower() in self._REQUIRES_REFRESH

    def _build_query(self) -> dict[str, str] | None:
        """构造 URL 中的 query 参数"""
        query: dict[str, str] = dict(parse_qsl(self.extra_query))

        if self.application_name:
            query.setdefault('application_name', self.application_name)

        if self.ssl_mode:
            key = self._SSL_MODE_KEYS.get(self.engine.lower(), 'ssl_mode')
            query.setdefault(key, self.ssl_mode)

        return query or None

    @cached_property
    def url_obj(self) -> URL:
        """构造并返回 SQLAlchemy 的 URL 对象

        使用 URL 对象而非字符串，可避免密码中特殊字符被误解。
        """
        drivername = f'{self.engine}+{self.driver}'
        query = self._build_query()

        # 文件型数据库：不拼 host/port/user/password
        if self.is_file_based:
            return URL.create(
                drivername=drivername,
                database=self.file_path or self.name,
                query=query,
            )

        # 网络型数据库：标准 host/port/user/password/database
        return URL.create(
            drivername=drivername,
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.name,
            query=query,
        )

    @cached_property
    def url(self) -> str:
        """构造并返回 SQLAlchemy 所需的数据库 URL 字符串

        Returns:
            拼接好的数据库连接 URL
        """
        return self.url_obj.render_as_string(hide_password=False)

    @cached_property
    def sync_url(self) -> str:
        """同步驱动 URL，供 Alembic 等同步工具使用

        Returns:
            同步驱动版本的数据库连接 URL
        """
        drivername = f'{self.engine}+{self._SYNC_DRIVERS.get(self.engine.lower(), self.driver)}'
        query = self._build_query()

        if self.is_file_based:
            return URL.create(
                drivername=drivername,
                database=self.file_path or self.name,
                query=query,
            ).render_as_string(hide_password=False)

        return URL.create(
            drivername=drivername,
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            database=self.name,
            query=query,
        ).render_as_string(hide_password=False)
