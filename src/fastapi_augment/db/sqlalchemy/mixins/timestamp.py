"""
@Author         : hangu
@CreateDate     : 2026/9/1
@Description    : 时间戳混入类，可整体或细粒度组合 created_at / updated_at 列
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class CreatedAtMixin:
    """创建时间混入类

    仅添加 created_at 一列，插入时由数据库时钟生成，之后不再变化
    适用于只增不改的表（日志、流水、快照等）
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='创建时间',
        sort_order=900
    )


class TimestampMixin(CreatedAtMixin):
    """时间戳混入类

    继承 CreatedAtMixin ，即常见的
    created_at / updated_at 成对出现；只要其中一列时，
    直接继承对应的细粒度混入类::

        class Log(CreatedAtMixin, ModelBase):   # 只要创建时间
            ...

        class User(TimestampMixin, ModelBase):  # 两列都要
            ...
    """
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment='更新时间',
        sort_order=910
    )
