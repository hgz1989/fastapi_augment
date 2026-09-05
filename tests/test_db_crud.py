"""
db.sqlalchemy.crud_base 模块测试 — CrudBase 通用 CRUD 操作

使用 aiosqlite 内存 SQLite 作为测试数据库
"""
import pytest
import pytest_asyncio
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi_augment.db.sqlalchemy.model_base import ModelBase
from fastapi_augment.db.sqlalchemy.crud_base import CrudBase
from fastapi_augment.db.sqlalchemy.mixins.timestamp import TimestampMixin
from fastapi_augment.db.sqlalchemy.mixins.soft_delete import SoftDeleteMixin

from sqlalchemy.orm import Mapped, mapped_column


# ── 测试模型 ──────────────────────────────────────────────────────────

class UserItem(TimestampMixin, SoftDeleteMixin, ModelBase):
    """测试用模型，包含时间戳和软删除"""
    __tablename__ = 'user_items'

    name: Mapped[str] = mapped_column(String(100), comment='名称')
    role: Mapped[str] = mapped_column(String(50), default='user', comment='角色')


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture()
async def engine():
    """创建内存 SQLite 异步引擎"""
    eng = create_async_engine('sqlite+aiosqlite://', echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(ModelBase.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture()
async def session(engine):
    """创建异步 session"""
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess


@pytest.fixture()
def crud() -> CrudBase[UserItem]:
    return CrudBase(UserItem)


# ── Create ────────────────────────────────────────────────────────────

class TestCrudCreate:

    async def test_create_single(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='alice', role='admin')
        result = await CrudBase.create(session, item)
        assert result.id is not None
        assert len(result.id) == 26  # ULID 长度

    async def test_create_many(self, session: AsyncSession, crud: CrudBase):
        items = [
            UserItem(name='bob', role='user'),
            UserItem(name='carol', role='user'),
        ]
        result = await CrudBase.create_many(session, items)
        assert len(result) == 2
        assert all(item.id is not None for item in result)


# ── Read ──────────────────────────────────────────────────────────────

class TestCrudRead:

    async def test_get_by_id(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='alice')
        await CrudBase.create(session, item)
        fetched = await crud.get(session, item.id)
        assert fetched is not None
        assert fetched.name == 'alice'

    async def test_get_nonexistent_returns_none(self, session: AsyncSession, crud: CrudBase):
        result = await crud.get(session, 'nonexistent_id')
        assert result is None

    async def test_get_one_with_filter(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='alice', role='admin'))
        await CrudBase.create(session, UserItem(name='bob', role='user'))

        result = await crud.get_one(session, name='bob')
        assert result is not None
        assert result.name == 'bob'

    async def test_get_one_no_match(self, session: AsyncSession, crud: CrudBase):
        result = await crud.get_one(session, name='nobody')
        assert result is None

    async def test_list_all(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='a'))
        await CrudBase.create(session, UserItem(name='b'))
        await CrudBase.create(session, UserItem(name='c'))

        results = await crud.list(session)
        assert len(results) == 3

    async def test_list_with_filter(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='a', role='admin'))
        await CrudBase.create(session, UserItem(name='b', role='user'))
        await CrudBase.create(session, UserItem(name='c', role='admin'))

        results = await crud.list(session, role='admin')
        assert len(results) == 2

    async def test_list_with_in_filter(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='a', role='admin'))
        await CrudBase.create(session, UserItem(name='b', role='user'))
        await CrudBase.create(session, UserItem(name='c', role='guest'))

        results = await crud.list(session, role=['admin', 'guest'])
        assert len(results) == 2

    async def test_list_with_limit(self, session: AsyncSession, crud: CrudBase):
        for i in range(5):
            await CrudBase.create(session, UserItem(name=f'item_{i}'))

        results = await crud.list(session, limit=3)
        assert len(results) == 3

    async def test_list_with_offset(self, session: AsyncSession, crud: CrudBase):
        for i in range(5):
            await CrudBase.create(session, UserItem(name=f'item_{i}'))

        results = await crud.list(session, offset=3, limit=None)
        assert len(results) == 2

    async def test_list_with_order_by_asc(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='charlie'))
        await CrudBase.create(session, UserItem(name='alice'))
        await CrudBase.create(session, UserItem(name='bob'))

        results = await crud.list(session, order_by=['name'], limit=None)
        names = [r.name for r in results]
        assert names == ['alice', 'bob', 'charlie']

    async def test_list_with_order_by_desc(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='alice'))
        await CrudBase.create(session, UserItem(name='charlie'))
        await CrudBase.create(session, UserItem(name='bob'))

        results = await crud.list(session, order_by=['-name'], limit=None)
        names = [r.name for r in results]
        assert names == ['charlie', 'bob', 'alice']


# ── Count / Exists ────────────────────────────────────────────────────

class TestCrudCountExists:

    async def test_count_all(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='a'))
        await CrudBase.create(session, UserItem(name='b'))
        assert await crud.count(session) == 2

    async def test_count_with_filter(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='a', role='admin'))
        await CrudBase.create(session, UserItem(name='b', role='user'))
        assert await crud.count(session, role='admin') == 1

    async def test_exists_true(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='alice'))
        assert await crud.exists(session, name='alice') is True

    async def test_exists_false(self, session: AsyncSession, crud: CrudBase):
        assert await crud.exists(session, name='nobody') is False


# ── Update ────────────────────────────────────────────────────────────

class TestCrudUpdate:

    async def test_update_instance(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='alice', role='user')
        await CrudBase.create(session, item)
        updated = await crud.update(session, item, name='alice_updated')
        assert updated.name == 'alice_updated'

    async def test_update_by_id(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='bob')
        await CrudBase.create(session, item)
        affected = await crud.update_by_id(session, item.id, name='bob_updated')
        assert affected == 1

        fetched = await crud.get(session, item.id)
        assert fetched.name == 'bob_updated'

    async def test_update_by_id_not_found(self, session: AsyncSession, crud: CrudBase):
        affected = await crud.update_by_id(session, 'nonexistent', name='x')
        assert affected == 0

    async def test_update_by_id_empty_values(self, session: AsyncSession, crud: CrudBase):
        affected = await crud.update_by_id(session, 'some_id')
        assert affected == 0

    async def test_update_invalid_field_raises(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='alice')
        await CrudBase.create(session, item)
        with pytest.raises(AttributeError, match='no mapped attribute'):
            await crud.update(session, item, nonexistent_field='value')


# ── Delete ────────────────────────────────────────────────────────────

class TestCrudDelete:

    async def test_delete_instance(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='alice')
        await CrudBase.create(session, item)
        await CrudBase.delete(session, item)
        assert await crud.get(session, item.id) is None

    async def test_delete_by_id(self, session: AsyncSession, crud: CrudBase):
        item = UserItem(name='bob')
        await CrudBase.create(session, item)
        result = await crud.delete_by_id(session, item.id)
        assert result is True
        assert await crud.get(session, item.id) is None

    async def test_delete_by_id_not_found(self, session: AsyncSession, crud: CrudBase):
        result = await crud.delete_by_id(session, 'nonexistent')
        assert result is False

    async def test_delete_where(self, session: AsyncSession, crud: CrudBase):
        await CrudBase.create(session, UserItem(name='a', role='temp'))
        await CrudBase.create(session, UserItem(name='b', role='temp'))
        await CrudBase.create(session, UserItem(name='c', role='keep'))

        deleted = await crud.delete_where(session, role='temp')
        assert deleted == 2
        assert await crud.count(session) == 1


# ── 辅助方法 ─────────────────────────────────────────────────────────

class TestCrudHelpers:

    def test_attr_valid(self, crud: CrudBase):
        attr = crud._attr('name')
        assert attr is not None

    def test_attr_invalid_raises(self, crud: CrudBase):
        with pytest.raises(AttributeError, match='no mapped attribute'):
            crud._attr('nonexistent')

    def test_conditions_with_expressions(self, session: AsyncSession, crud: CrudBase):
        """raw expressions 被正确合并"""
        conditions = crud._conditions(
            expressions=(UserItem.name == 'test',),
            filters={'role': 'admin'},
        )
        assert len(conditions) == 2

    def test_conditions_none_value_becomes_is_null(self, crud: CrudBase):
        """None 值过滤条件"""
        conditions = crud._conditions(None, {'name': None})
        assert len(conditions) == 1

    def test_resolve_order_string_asc(self, crud: CrudBase):
        result = crud._resolve_order('name')
        assert result is not None

    def test_resolve_order_string_desc(self, crud: CrudBase):
        result = crud._resolve_order('-name')
        assert result is not None

    def test_resolve_order_with_plus_prefix(self, crud: CrudBase):
        result = crud._resolve_order('+name')
        assert result is not None

    def test_resolve_order_column_expression(self, crud: CrudBase):
        col_expr = UserItem.name.asc()
        result = crud._resolve_order(col_expr)
        assert result is col_expr


# ── Paginate ──────────────────────────────────────────────────────────

class TestCrudPaginate:

    async def test_paginate_returns_dict(self, session: AsyncSession, crud: CrudBase):
        """paginate 返回正确的分页字典结构"""
        for i in range(5):
            await CrudBase.create(session, UserItem(name=f'user_{i}', role='user'))

        result = await crud.paginate(session, page=1, size=3)

        assert result['page'] == 1
        assert result['size'] == 3
        assert result['total'] == 5
        assert result['pages'] == 2
        assert len(result['items']) == 3

    async def test_paginate_second_page(self, session: AsyncSession, crud: CrudBase):
        """paginate 第二页数据正确"""
        for i in range(5):
            await CrudBase.create(session, UserItem(name=f'user_{i}', role='user'))

        result = await crud.paginate(session, page=2, size=3)

        assert result['page'] == 2
        assert result['total'] == 5
        assert result['pages'] == 2
        assert len(result['items']) == 2

    async def test_paginate_with_filters(self, session: AsyncSession, crud: CrudBase):
        """paginate 过滤条件同时作用于 count 和 list"""
        await CrudBase.create(session, UserItem(name='admin', role='admin'))
        await CrudBase.create(session, UserItem(name='user1', role='user'))
        await CrudBase.create(session, UserItem(name='user2', role='user'))

        result = await crud.paginate(session, page=1, size=10, role='admin')

        assert result['total'] == 1
        assert len(result['items']) == 1
        assert result['items'][0].name == 'admin'

    async def test_paginate_empty(self, session: AsyncSession, crud: CrudBase):
        """无数据时返回空列表、total=0"""
        result = await crud.paginate(session, page=1, size=10)

        assert result['total'] == 0
        assert result['pages'] == 0
        assert len(result['items']) == 0

    async def test_paginate_with_order(self, session: AsyncSession, crud: CrudBase):
        """paginate 支持排序"""
        await CrudBase.create(session, UserItem(name='charlie', role='user'))
        await CrudBase.create(session, UserItem(name='alice', role='user'))
        await CrudBase.create(session, UserItem(name='bob', role='user'))

        result = await crud.paginate(session, page=1, size=10, order_by=['name'])

        names = [item.name for item in result['items']]
        assert names == ['alice', 'bob', 'charlie']
