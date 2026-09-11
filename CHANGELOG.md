# 更新日志

本文件记录 `fastapi-augment` 各版本的变更内容，格式遵循 [Keep a Changelog](https://keepachangelog.com/)。

---

## [0.1.3] — 2026-09-11

### Added

- **查询解析器 `query_parser`** — 新增 REST 风格 query string 转 SQLAlchemy `ColumnElement` 表达式模块
  - `parse_where` — FIQL 风格组合条件，支持 `==` `!=` `~=` `>` `>=` `<` `<=` `~between~` 八种操作符，`;` AND / `,` OR / `()` 括号分组
  - `parse_lookup` — 精确匹配端点过滤器，`;` 分隔多条件 AND，字段白名单 + 防重复校验
  - `parse_keyword` — 多字段 OR 模糊搜索（ILIKE）
  - `parse_sort` — 排序解析，`-field` 降序 / `field` 升序
  - `build_query_expressions` — 一键组合 where + keyword + sort，直接传入 `paginate` / `list` 的 `expressions` / `order_by` 参数
- **`RepositoryBase.get_unique`** — 精确唯一查询，多条匹配时抛出 `MultipleResultsFound`，区别于 `get_first`（取第一条）

### Changed

- **`RepositoryBase`** — `get_one` 拆分为语义更清晰的两个方法：
  - `get_first` — 取第一条匹配记录（`.limit(1)` + `.scalars().first()`），无匹配返回 `None`
  - `get_unique` — 精确唯一匹配，多条匹配抛出异常
- **`create_app()`** — 调整 FastAPI 参数顺序，新增 `summary` 摘要字段支持

### Removed

- **`openapi_enable_bearer_auth`** — 移除 Bearer 认证自动注入功能（`OpenAPICustomConfig` 不再包含 `enable_bearer_auth` / `bearer_auth_name`）

### Fixed

- **`RepositoryBase.__init__`** — 修复初始化时模型类型赋值问题

---

## [0.1.2] — 2026-09-09

### Added

- **`common.utils.paths`** — 新增路径工具函数模块
- **`common.utils` 导出** — `__init__.py` 统一导出路径和字符串工具函数

### Changed

- **构建配置** — 更新 `pyproject.toml` 打包配置

---

## [0.1.1] — 2026-09-07

### Added

- **CI/CD 测试步骤** — `publish.yml` 新增 pytest 测试 Job（Python 3.11 / 3.12 / 3.13 矩阵），发布流程依赖测试通过
- **`test_model_base.py`** — 新增 8 个 `ModelBase` 单元测试
- **`test_settings.py`** — 新增 8 个 `EnvSettings` 配置管理测试
- **`test_migrate.py`** — 新增 10 个数据库迁移 CLI 测试
- **`RepositoryBase` 完整测试** — 46 个测试覆盖 CRUD、过滤、排序、分页、子类继承、异常处理

### Changed

- **`CrudBase` → `RepositoryBase`** — 重命名仓储基类，语义更准确
- **`RepositoryBase` 增强** — 新增 `paginate`、`delete_where`、`update_by_id` 等方法；支持 IN 列表过滤、IS NULL 检查
- **`SessionFactory`** — 优化缓存机制与读写分离逻辑
- **`factory.py`** — 改进 `Any` 类型为 `TYPE_CHECKING` 导入，提升类型安全
- **`db/__init__.py`** — 完善文档注释
- **`README.md`** — 全面重写文档，补充 `WeakKeyDictionary` 注意事项

### Fixed

- **日志处理器** — 修复多进程场景下轮转文件处理器的兼容性问题

---

## [0.1.0] — 2026-09-07

首个公开发布版本。

### 核心模块

| 模块 | 说明 |
| --- | --- |
| `factory.py` | `create_app()` 应用工厂，一行代码创建 FastAPI 实例 |
| `lifespan.py` | `HookRegistry` 生命周期管理，优先级 / 超时 / 异常策略 |
| `db/sqlalchemy/engine.py` | `EngineManager` 异步引擎管理，单库 / 主从 / 集群拓扑 |
| `db/sqlalchemy/session.py` | `SessionFactory` 读写分离会话工厂 |
| `db/sqlalchemy/model_base.py` | `ModelBase` ULID 主键声明式基类 |
| `db/sqlalchemy/crud_base.py` | `CrudBase` 泛型异步仓储基类 |
| `db/sqlalchemy/migrate.py` | `fastapi-augment-migrate` Alembic 迁移 CLI |
| `db/sqlalchemy/mixins/` | `TimestampMixin` / `AuditMixin` / `SoftDeleteMixin` 等可组合 Mixin |
| `schemas/` | `APIResponse` 统一响应、`PageData` 分页模型、请求参数模型 |
| `common/exceptions.py` | 完整 4xx HTTP 异常子类体系 |
| `common/exception_handlers.py` | 全局异常处理器，自动返回标准格式 |
| `log/` | request_id 注入、uvicorn 接管、多进程安全轮转、幂等初始化 |
| `health/` | 可扩展检查器模式，内置应用状态 + 数据库连通性检查 |
| `config/settings.py` | `EnvSettings` 基于 pydantic-settings 的配置管理 |
| `middlewares/` | `RequestIdMiddleware`（ULID 格式），`ContextVar` 全链路传递 |
| `openapi.py` | OpenAPI schema 自动清理 422 响应与验证错误模型 |

[Latest]: https://github.com/hgz1989/fastapi-augment/compare/v0.1.3...develop
[0.1.3]: https://github.com/hgz1989/fastapi-augment/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/hgz1989/fastapi-augment/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/hgz1989/fastapi-augment/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/hgz1989/fastapi-augment/releases/tag/v0.1.0
