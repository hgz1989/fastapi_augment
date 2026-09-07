import asyncio
import importlib
from logging import getLogger
from logging.config import fileConfig
from os import environ
from urllib.parse import urlparse

from alembic import context
from sqlalchemy import Connection, pool, engine_from_config
from sqlalchemy.ext.asyncio import async_engine_from_config

from fastapi_augment.db.sqlalchemy import Base

_logger = getLogger(__name__)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 从 alembic.ini 读取自定义版本表名称，如果没有则使用默认名
version_table = config.get_main_option('version_table', 'migration_version')

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

# 从环境变量 FASTAPI_AUGMENT_MODELS 动态导入用户模型模块，
# 使模型注册到 Base.metadata，autogenerate 才能检测到变更。
_models_env = environ.get('FASTAPI_AUGMENT_MODELS', '')
if _models_env:
    for _mod in _models_env.split(','):
        _mod = _mod.strip()
        if _mod:
            try:
                importlib.import_module(_mod)
            except ImportError as _e:
                _logger.warning('无法导入模型模块 %s: %s', _mod, _e)

target_metadata = Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run alembic in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        version_table=version_table,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """内部实际执行迁移的函数

    Args:
        connection: SQLAlchemy 数据库连接对象
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table=version_table
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移

    创建异步引擎并关联连接至上下文
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run alembic in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = config.get_main_option('sqlalchemy.url')
    if not url:
        raise ValueError('SQLAlchemy URL 未设置')

    async_drivers = {'asyncpg', 'asyncmy', 'aiomysql', 'aiosqlite', 'aioodbc'}
    is_async = urlparse(url).scheme.split('+')[-1] in async_drivers

    if is_async:
        asyncio.run(run_async_migrations())
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix='sqlalchemy.',
            poolclass=pool.NullPool,
        )
        with connectable.connect() as connection:
            do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
