# fastapi-augment

基于 FastAPI 封装的生产级 Web 应用框架，提供开箱即用的数据库引擎管理、异步 Session、通用 Mixin 与统一响应模型。

## 安装

```bash
pip install fastapi_augment

# 如需 SQLAlchemy 支持
pip install fastapi_augment[sqlalchemy]
```

## 核心模块

### db.sqlalchemy — 异步数据库层

- **EngineManager** — 单库 / 主从 / 集群拓扑的异步引擎生命周期管理
- **SessionFactory** — 读写分离的异步 Session 工厂，支持 FastAPI `Depends()` 注入
- **CrudBase** — 泛型异步 CRUD 仓库（create / get / list / update / delete / count / exists）
- **ModelBase** — 基于 ULID 主键的模型基类

### db.sqlalchemy.mixins — 可组合列混入

| Mixin | 提供的列 |
|---|---|
| `CreatedAtMixin` | `created_at` |
| `TimestampMixin` | `created_at` + `updated_at` |
| `CreatedByMixin` | `created_by` |
| `UpdatedByMixin` | `updated_by` |
| `AuditMixin` | `created_by` + `updated_by` |
| `SoftDeleteMixin` | `is_deleted` + `deleted_at` |

### schemas — 统一请求 / 响应模型

- **APIResponse** — 全局统一返回格式（`request_id` / `code` / `message` / `data` / `extra`）
- **PageData** — 通用分页响应
- **PageParams / TimeRangeParams / KeywordParams** — 常用请求参数
- 全局驼峰别名、时间序列化开箱即用

## 快速开始

```python
from fastapi_augment.db.sqlalchemy import (
    ClusterTopology, EngineManager, NodeConfig,
    SessionFactory, ModelBase, CrudBase, TimestampMixin,
)

# 1. 配置拓扑
topology = ClusterTopology(
    primary=NodeConfig(url='postgresql+asyncpg://user:pass@host/db'),
)
manager = EngineManager(topology).start()
factory = SessionFactory(manager)

# 2. 定义模型
class User(TimestampMixin, ModelBase):
    __tablename__ = 'users'

# 3. 使用 CRUD
async with factory.transaction() as session:
    crud = CrudBase(User)
    user = await crud.create(session, User(name='alice'))
```

## 许可证

MIT
