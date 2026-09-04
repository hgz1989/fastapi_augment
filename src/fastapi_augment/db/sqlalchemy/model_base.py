"""
@Author         : hangu
@CreateDate     : 2026/8/31
@Description    : SQLAlchemy 模型基础类
"""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from .base import Base


def _generate_ulid() -> str:
    """生成ULID

    Returns:
        ULID字符串
    """
    return str(ULID()).lower()


class ModelBase(Base):
    """SQLAlchemy模型基础类

    仅提供通用的 ULID 主键字段；时间戳、软删除、审计等
    通用列通过 mixins 按需组合，成对的列可整体使用，
    也可用细粒度混入类只取其中一列：

        from .mixins import (
            CreatedAtMixin, SoftDeleteMixin, TimestampMixin,
        )

        class User(TimestampMixin, SoftDeleteMixin, ModelBase):
            ...                                             # created_at + updated_at

        class Log(CreatedAtMixin, ModelBase):              # 只要创建时间
            ...
    """
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(26),
        default=_generate_ulid,
        primary_key=True,
        comment='主键ID',
        sort_order=-1
    )
