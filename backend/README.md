# 公司内部内容自动发布平台后端

基于 PostgreSQL 的公司内部内容提交、审核、自动发布和检索 REST API。后端负责权限校验、业务状态机、文件安全、发布目录写入与审计；前端只消费 API 返回的数据和 `view_url`。

## 技术栈与运行要求

- Python 3.12+
- FastAPI、Pydantic v2
- SQLAlchemy 2.0 同步 ORM
- PostgreSQL 15+（仅支持 PostgreSQL，不提供 SQLite 回退）
- psycopg 3
- Alembic
- PyJWT、pwdlib Argon2
- pytest、httpx

## 1. 创建 PostgreSQL 数据库

以有创建数据库权限的 PostgreSQL 账号执行：

```sql
CREATE DATABASE content_publish;
CREATE DATABASE content_publish_test;
```

`content_publish_test` 必须是与开发、生产库隔离的专用测试库。测试夹具会清理并重建其中的六张业务表，绝不能把 `TEST_DATABASE_URL` 指向开发库或生产库。

## 2. 创建虚拟环境并安装依赖

Windows PowerShell：

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux：

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. 配置 `.env`

复制示例并修改账号、密码和密钥：

```powershell
Copy-Item .env.example .env
```

关键配置：

```env
APP_ENV=development
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish
TEST_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish_test
JWT_SECRET_KEY=replace-with-a-long-random-production-secret
SOURCE_STORAGE_ROOT=../local-data/source
PREVIEW_STORAGE_ROOT=../local-data/preview
LOCAL_PUBLISHED_ROOT=../local-data/published
MAX_UPLOAD_SIZE_MB=100
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DB_CONNECT_TIMEOUT_SECONDS=5
```

- `DATABASE_URL`：应用和 Alembic 使用的 PostgreSQL 连接串，驱动必须为 `postgresql+psycopg`。
- `TEST_DATABASE_URL`：pytest 专用 PostgreSQL 数据库，不能与 `DATABASE_URL` 相同。
- `JWT_SECRET_KEY`：生产环境必须替换为随机长密钥，不能提交 `.env`。
- `SOURCE_STORAGE_ROOT`：上传源文件目录；发布器不会把它直接暴露为静态目录。
- `CORS_ORIGINS`：多个来源用逗号分隔。

## 4. Alembic Migration

创建表或升级数据库：

```bash
alembic upgrade head
```

检查当前版本和迁移历史：

```bash
alembic current
alembic history
```

初始迁移创建且仅创建六张业务表：`users`、`contents`、`publish_targets`、`review_records`、`publish_records`、`operation_logs`，并包含 PostgreSQL `JSONB`、`TIMESTAMPTZ`、约束、索引及外键。

## 5. Seed 开发数据

先完成 Migration，再执行：

```bash
python scripts/seed.py
```

Seed 可重复执行，创建开发账号与六类本地发布目标：

| 角色 | 用户名 | 开发密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 普通员工 | `employee` | `employee123` |

这些密码仅用于本地开发，部署前必须禁用或修改。

## 6. 启动 FastAPI

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- 健康检查：`http://localhost:8000/api/health`
- Swagger UI：`http://localhost:8000/docs`
- OpenAPI JSON：`http://localhost:8000/openapi.json`

前端真实 API 模式使用：

```env
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8000/api
```

## 7. 运行 pytest

确认 `TEST_DATABASE_URL` 指向可丢弃的独立测试库，然后运行：

```bash
pytest -q
pytest --cov=app --cov-report=term-missing
```

测试启动时会同时校验：

1. 数据库必须是 PostgreSQL。
2. `TEST_DATABASE_URL` 不能与 `DATABASE_URL` 相同。
3. 测试库不可用时 PostgreSQL 集成测试会明确跳过，单元测试仍会运行。

覆盖范围包括认证与禁用 Token、角色权限、数据库约束、内容状态流转、驳回重提、发布成功/失败、重新发布、目录越界、文件类型与大小、员工字段脱敏、搜索、审计记录和八个 Publisher。

## 8. 用户角色与权限

- `admin`：用户管理、审核、直接发布、重新发布、发布目标配置、全量日志和后台统计。
- `employee`：维护自己的可编辑内容、提交审核、查看自己的记录、检索已发布内容。
- 被禁用用户无法登录；已有 JWT 每次访问也会重新检查用户状态并返回 403。
- 员工读取发布目标时不会收到服务器物理路径 `publish_root`。

## 9. 内容与发布状态

内容审核状态：

```text
draft -> pending -> approved
                  -> rejected -> pending
```

内容发布状态：

```text
unpublished -> publishing -> published
                          -> failed -> publishing
```

审核通过采用两阶段事务：事务 A 锁定内容并提交 `approved/publishing`、审核记录、发布记录和操作日志；文件发布在事务外执行；事务 B 写入成功或失败结果。失败时审核状态仍保持 `approved`，可由管理员重新发布，每次尝试都会产生新的 `publish_records` 记录。

## 10. 文件存储与发布目录

上传源文件保存在：

```text
local-data/source/{content_id}/{uuid}.{ext}
```

上传会校验文件名、扩展名、大小和最终解析路径，拒绝绝对路径、`..`、斜杠及反斜杠逃逸。源文件目录不会挂载为公开静态目录。

发布目标由管理员配置：

- `content_types`：该目标允许的内容类型，数据库使用 PostgreSQL `JSONB`。
- `publish_root`：服务器物理输出根目录，只向管理员返回。
- `base_url`：外部访问 URL 根地址。
- `enabled`：停用后不能用于新发布；已有记录引用的目标不能物理删除。

最终目录名为安全的 `{content_id}-{slug}`。后端在验证 `publish_root` 后写入目录，并基于 `base_url` 返回 `view_url`；前端不得读取物理路径或自行拼接 URL。本地 Seed 目标位于 `local-data/published/`，仅在 `APP_ENV=development` 时由 FastAPI 的 `/local-published` 静态路径提供开发访问。

## 11. Publisher 架构与扩展

`app/publishers/` 包含统一 `BasePublisher`、`PublishResult` 和八个实现：HTML、Dynamic、PPT、PDF、Word、Excel、Image、File。Publisher 只负责生成文件并返回相对路径、物理输出路径和访问 URL；数据库状态统一由 `PublishService` 管理。

新增内容类型的 Publisher：

1. 在 `app/core/constants.py` 增加类型及允许的文件扩展名。
2. 在 `app/publishers/` 新建类并继承 `BasePublisher`。
3. 实现 `publish(content, target) -> PublishResult`，使用 `prepare_output` 和 `safe_child` 做目录约束。
4. 在 `PublisherFactory._publishers` 注册映射。
5. 在数据库约束的 Alembic Migration 中加入新枚举值，并补充成功、失败与路径安全测试。

不要在 Publisher 内直接提交数据库事务，也不要在 API Router 中实现文件转换逻辑。

## 12. 项目结构

```text
backend/
├─ alembic/                 # PostgreSQL migrations
├─ app/
│  ├─ api/                  # 路由与依赖
│  ├─ core/                 # 配置、安全、枚举、异常
│  ├─ db/models/            # 六张业务表 ORM
│  ├─ publishers/           # 八个内容发布器
│  ├─ repositories/         # SQL 查询和持久化
│  ├─ schemas/              # Pydantic 请求/响应模型
│  ├─ services/             # 业务状态机和事务边界
│  └─ utils/                # 时间、文件、路径、slug
├─ scripts/seed.py
├─ ../local-data/source/    # 本地配置的私有上传源文件（可通过环境变量调整）
├─ tests/                   # 单元测试和 PostgreSQL 集成测试
├─ .env.example
├─ alembic.ini
├─ pytest.ini
└─ requirements.txt
```

生产部署应由反向代理或对象存储/CDN 提供最终发布文件，并让 `base_url` 指向真实访问地址；不要假设生产发布目录与 Seed 的本地目录相同。
