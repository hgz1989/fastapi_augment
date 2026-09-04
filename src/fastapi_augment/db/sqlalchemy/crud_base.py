"""
@Author         : hangu
@CreateDate     : 2026/8/31
@Description    : Generic async CRUD base with create / read / update / delete operations.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import ColumnExpressionArgument, delete, exists, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from .model_base import ModelBase

ModelT = TypeVar('ModelT', bound=ModelBase)


class CrudBase(Generic[ModelT]):
    """Generic CRUD repository for :class:`ModelBase` subclasses.

    The session is always passed explicitly, so callers keep full control
    of the transaction boundary — CRUD methods only *flush*, never *commit*::

        user_crud = CrudBase(User)

        async with factory.transaction() as session:      # auto commit
            await user_crud.create(session, User(name="alice"))

        async with factory.read_session() as session:     # read replica
            users = await user_crud.list(session, is_active=True, limit=10)

    Filters accept both keyword arguments and raw SQLAlchemy expressions::

        await user_crud.list(session, role="admin", expressions=(User.age > 18,))
        await user_crud.list(session, id=["01A", "02B"])   # sequence -> IN
        await user_crud.list(session, name=None)           # None -> IS NULL
    """

    def __init__(self, model: type[ModelT]) -> None:
        self.model = model

    # ── Create ───────────────────────────────────────────────────────────

    async def create(self, session: AsyncSession, obj: ModelT) -> ModelT:
        """Persist a new object. Flushes so PKs / defaults are populated; never commits."""
        session.add(obj)
        await session.flush()
        return obj

    async def create_many(self, session: AsyncSession, objs: Sequence[ModelT]) -> list[ModelT]:
        """Persist multiple objects in one batch. Flushes; never commits."""
        session.add_all(objs)
        await session.flush()
        return list(objs)

    # ── Read ─────────────────────────────────────────────────────────────

    async def get(self, session: AsyncSession, id: str) -> ModelT | None:
        """Fetch a single row by primary key (checks the session identity map first)."""
        return await session.get(self.model, id)

    async def get_one(
        self,
        session: AsyncSession,
        *,
        expressions: Sequence[ColumnExpressionArgument[bool]] | None = None,
        **filters: Any,
    ) -> ModelT | None:
        """Fetch the first row matching the filters, or ``None``."""
        stmt = select(self.model).where(*self._conditions(expressions, filters)).limit(1)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def list(
        self,
        session: AsyncSession,
        *,
        expressions: Sequence[ColumnExpressionArgument[bool]] | None = None,
        order_by: Sequence[str | ColumnExpressionArgument[Any]] | None = None,
        offset: int = 0,
        limit: int | None = 100,
        **filters: Any,
    ) -> list[ModelT]:
        """Fetch rows matching the filters with optional ordering / pagination.

        Args:
            session: Async session to run the query on (use a read session).
            expressions: Raw SQLAlchemy filter expressions.
            order_by: Column expressions or field names; prefix a name with
                ``-`` for descending order (e.g. ``'-created_at'``).
            offset: Number of rows to skip.
            limit: Max rows to return (``None`` = no limit).
            **filters: Equality keyword filters.
        """
        stmt = select(self.model).where(*self._conditions(expressions, filters))
        if order_by:
            stmt = stmt.order_by(*(self._resolve_order(spec) for spec in order_by))
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        session: AsyncSession,
        *,
        expressions: Sequence[ColumnExpressionArgument[bool]] | None = None,
        **filters: Any,
    ) -> int:
        """Count rows matching the filters."""
        stmt = select(func.count()).select_from(self.model).where(*self._conditions(expressions, filters))
        result = await session.execute(stmt)
        return result.scalar_one()

    async def exists(
        self,
        session: AsyncSession,
        *,
        expressions: Sequence[ColumnExpressionArgument[bool]] | None = None,
        **filters: Any,
    ) -> bool:
        """Return ``True`` if at least one row matches the filters."""
        stmt = select(exists().where(*self._conditions(expressions, filters)))
        result = await session.execute(stmt)
        return bool(result.scalar())

    # ── Update ───────────────────────────────────────────────────────────

    async def update(self, session: AsyncSession, obj: ModelT, **values: Any) -> ModelT:
        """Update an ORM instance in place. Flushes; never commits."""
        for key in values:
            self._attr(key)
        for key, value in values.items():
            setattr(obj, key, value)
        await session.flush()
        return obj

    async def update_by_id(self, session: AsyncSession, id: str, **values: Any) -> int:
        """Update a row by primary key with a single UPDATE statement.

        Returns the number of affected rows (0 = not found or nothing to update).
        """
        if not values:
            return 0
        stmt = update(self.model).where(self.model.id == id).values(**values)
        result = await session.execute(stmt)
        return result.rowcount or 0

    # ── Delete ───────────────────────────────────────────────────────────

    async def delete(self, session: AsyncSession, obj: ModelT) -> None:
        """Delete an ORM instance. Flushes; never commits."""
        await session.delete(obj)
        await session.flush()

    async def delete_by_id(self, session: AsyncSession, id: str) -> bool:
        """Delete a row by primary key. Returns ``True`` if a row was deleted."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await session.execute(stmt)
        return bool(result.rowcount)

    async def delete_where(
        self,
        session: AsyncSession,
        *,
        expressions: Sequence[ColumnExpressionArgument[bool]] | None = None,
        **filters: Any,
    ) -> int:
        """Delete all rows matching the filters. Returns the number of deleted rows."""
        stmt = delete(self.model).where(*self._conditions(expressions, filters))
        result = await session.execute(stmt)
        return result.rowcount or 0

    # ── Helpers ──────────────────────────────────────────────────────────

    def _attr(self, name: str) -> InstrumentedAttribute[Any]:
        """Resolve a field name to a mapped attribute, failing fast on typos."""
        attr = getattr(self.model, name, None)
        if not isinstance(attr, InstrumentedAttribute):
            raise AttributeError(f'{self.model.__name__} has no mapped attribute {name!r}')
        return attr

    def _conditions(
        self,
        expressions: Sequence[ColumnExpressionArgument[bool]] | None,
        filters: Mapping[str, Any],
    ) -> list[ColumnExpressionArgument[bool]]:
        """Combine raw expressions and keyword filters into WHERE conditions."""
        conditions: list[ColumnExpressionArgument[bool]] = list(expressions or [])
        for key, value in filters.items():
            column = self._attr(key)
            if isinstance(value, (list, set, tuple, frozenset)):
                conditions.append(column.in_(value))
            else:
                conditions.append(column == value)
        return conditions

    def _resolve_order(self, spec: str | ColumnExpressionArgument[Any]) -> ColumnExpressionArgument[Any]:
        """Convert an order-by spec into a column expression."""
        if isinstance(spec, str):
            descending = spec.startswith('-')
            column = self._attr(spec.lstrip('+-'))
            return column.desc() if descending else column.asc()
        return spec
