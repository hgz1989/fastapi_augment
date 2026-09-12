"""
@Author         : hangu
@CreateDate     : 2026/9/1
@Description    : 审计混入类，可整体或细粒度组合 created_by / updated_by 列
"""
from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class CreatedByMixin:
    """创建人混入类

    仅添加 created_by 一列，记录创建操作人ID，
    默认对齐 ModelBase 的 ULID 主键长度（String(26)）
    """

    created_by: Mapped[str | None] = mapped_column(
        String(26),
        default=None,
        comment='创建人ID',
        sort_order=901
    )


class UpdatedByMixin:
    """更新人混入类

    仅添加 updated_by 一列，记录最近更新操作人ID
    """

    updated_by: Mapped[str | None] = mapped_column(
        String(26),
        default=None,
        comment='更新人ID',
        sort_order=911
    )


class AuditMixin(CreatedByMixin, UpdatedByMixin):
    """审计混入类

    组合 CreatedByMixin + UpdatedByMixin，即常见的
    created_by / updated_by 成对出现；只要其中一列时，
    直接继承对应的细粒度混入类::

        class Article(CreatedByMixin, ModelBase):  # 只记录创建人
            ...

    两列均为可空：系统任务（无登录用户上下文）写入时留空；
    由 service 层从当前请求上下文取用户ID填充::

        await repo.create(
            session,
            User(name='alice', created_by=current_user.id),
        )
        await repo.update_by_id(
            session, uid, updated_by=current_user.id, **changes,
        )
    """
