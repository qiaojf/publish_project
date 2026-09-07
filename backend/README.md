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

`content_publish_test` 必须是与开发、生产库隔离的专用测试库。测试夹具会清理并重建其中的七张业务表，绝不能把 `TEST_DATABASE_URL` 指向开发库或生产库。

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
MAX_UPLOAD_SIZE_MB=1024
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

迁移创建七张业务表：`users`、`categories`、`contents`、`publish_targets`、`review_records`、`publish_records`、`operation_logs`，并包含 PostgreSQL `JSONB`、`TIMESTAMPTZ`、约束、索引及外键。

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

覆盖范围包括认证与禁用 Token、角色权限、数据库约束、内容状态流转、驳回重提、发布成功/失败、重新发布、目录越界、文件类型与大小、员工字段脱敏、搜索、审计记录、内容处理器和六类发布目标 Adapter。

## 8. 用户角色与权限

- `admin`：用户管理、分类配置、审核、直接发布、重新发布、发布目标配置、全量日志和后台统计。
- `employee`：维护自己的可编辑内容、提交审核、查看自己的记录、检索已发布内容。
- 被禁用用户无法登录；已有 JWT 每次访问也会重新检查用户状态并返回 403。
- 员工读取发布目标时不会收到服务器物理路径 `publish_root`。

管理员通过 `GET/POST/PUT/PATCH/DELETE /api/categories` 管理分类。重命名会在同一事务中同步更新已有内容；已被内容引用的分类不能删除，但可以禁用。员工以及内容表单只读取已启用分类。

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

## 10. 多文件与文件夹上传

前端可一次选择多个文件，或选择一个文件夹并保留相对目录结构。后端把一个内容的源文件保存在独立 UUID 目录中，并在 `contents.source_files` JSONB 中仅记录文件名、相对路径和大小。上传总大小受 `MAX_UPLOAD_SIZE_MB` 限制；绝对路径、`..`、重复路径和越界路径都会被拒绝。

多个文件或文件夹的详情预览只返回文件清单，不解析文件正文；单个 PDF、图片仍在线预览，PPT 统一按普通文件显示名称和下载入口。

## 11. 多发布目标架构

发布职责分为两层：

```text
Content -> ContentProcessorFactory -> PublishArtifact
        -> PublishService -> TargetPublisherFactory -> TargetPublishResult
```

- `app/content_processors/`：按 HTML、Dynamic、PPT、PDF、Word、Excel、Image、File 生成与目标无关的 Artifact。
- `app/target_publishers/`：独立实现 `local`、`sftp`、`github`、`github_pages`、`onedrive`、`dropbox`。
- `PublishService`：只编排处理器和目标 Adapter，统一写入内容状态和 `publish_records`。
- OneDrive 与 Dropbox 收到目录 Artifact 时由 `ArtifactPackagingService` 自动压缩为 ZIP。

`publish_targets` 的通用字段：

- `target_type`：上述六种固定类型，数据库有 CHECK Constraint。
- `content_types`：允许发布的内容类型。
- `config`：平台非敏感 JSONB 配置。
- `credential_ref`：环境变量凭证引用名。
- `publish_root`、`base_url`：继续供 Local 目标使用，兼容已有数据。

各类型 `config`：

| 类型 | 非敏感配置 |
|---|---|
| Local | `publish_root`、`base_url`（旧字段） |
| SFTP | `host`、`port`、`username`、`remote_root`、`base_url` |
| GitHub | `owner`、`repo`、`branch`、`repo_path` |
| GitHub Pages | GitHub 字段及 `base_url` |
| OneDrive | `tenant_id`、`client_id`、`drive_id`、`folder_path` |
| Dropbox | `folder_path` |

管理员可调用 `POST /api/publish-targets/{id}/test` 测试连接；此操作不发布内容，也不创建 `PublishRecord`。自动测试使用 Mock Transport / Fake SFTP，不会访问真实第三方账号。

GitHub Pages 目标会校验配置的 Branch 是否与仓库实际的 Pages 发布分支一致。发布时系统在提交文件后继续等待对应 commit 构建完成，只有 Pages 部署成功才记录发布成功并返回访问地址。

GitHub Repository 目标会在单文件超过普通 Git 100 MiB 限制时自动通过 Git LFS Batch API 上传，并向仓库提交 LFS 指针和 `.gitattributes`。GitHub Pages 官方不支持 Git LFS，因此 Pages 目标会在提交前拒绝此类大文件并给出替代目标提示，避免部署出只有指针或空内容的页面。

## 12. 凭证与安全

Token、密码、Client Secret、私钥和 Passphrase 禁止写入 `config`。`CredentialService` 按以下规则在真正连接目标时延迟读取凭证：优先使用操作系统进程环境变量，未设置时读取 `backend/.env`。

```text
credential_ref=github_company_pages + key=token
-> PUBLISH_CREDENTIAL_GITHUB_COMPANY_PAGES_TOKEN
```

常用示例：

```env
PUBLISH_CREDENTIAL_GITHUB_COMPANY_PAGES_TOKEN=...
PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET=...
PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN=...
PUBLISH_CREDENTIAL_SFTP_INTERNAL_PASSWORD=...
PUBLISH_CONNECTION_TIMEOUT_SECONDS=30
PUBLISH_OPERATION_TIMEOUT_SECONDS=600
```

GET API 和日志永远不返回 Secret；普通员工响应只包含目标 `id`、`name`、`target_type`、`content_types`、`enabled`。外部凭证缺失不影响应用启动或 Local 发布，只有调用对应远程目标时才返回脱敏错误。

GitHub、OneDrive 和 Dropbox 的 HTTPS 请求使用操作系统证书存储进行 TLS 校验，兼容由公司 Windows 证书策略管理的代理或根证书；系统不会通过关闭证书校验来绕过连接问题。

第三方实现依据官方接口：[GitHub Git Data REST API](https://docs.github.com/en/rest/git)、[GitHub 大文件限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)、[GitHub LFS 与 Pages 限制](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage)、[Microsoft Graph 文件上传](https://learn.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0)、[Dropbox 上传会话](https://developers.dropbox.com/dbx-performance-guide) 与 [Paramiko SFTP](https://docs.paramiko.org/en/stable/api/sftp.html)。

## 13. 新增发布平台

以后增加 S3、Azure Blob、Google Drive 或 NAS 时，只需：

1. 增加 `target_type` 与配置校验。
2. 实现 `BaseTargetPublisher`。
3. 注册 `TargetPublisherFactory`。
4. 在管理员动态表单增加字段。
5. 补充完全 Mock 的连接、上传、失败和重试测试。

无需修改员工提交、管理员审核、Content、ReviewRecord 或主发布流程。

## 14. 项目结构

```text
backend/
├─ alembic/                 # PostgreSQL migrations
├─ app/
│  ├─ api/                  # 路由与依赖
│  ├─ core/                 # 配置、安全、枚举、异常
│  ├─ db/models/            # 七张业务表 ORM
│  ├─ content_processors/   # 内容处理与 Artifact 生成
│  ├─ target_publishers/    # 六种可插拔目标 Adapter
│  ├─ publishers/           # 旧内容发布器兼容层
│  ├─ repositories/         # SQL 查询和持久化
│  ├─ schemas/              # Pydantic 请求/响应模型
│  ├─ services/             # 业务状态机和事务边界
│  └─ utils/                # 时间、文件、路径、slug
├─ scripts/seed.py
├─ ../local-data/source/    # 私有上传源文件
├─ ../local-data/build/     # 与目标无关的临时 Artifact
├─ tests/                   # 单元测试和 PostgreSQL 集成测试
├─ .env.example
├─ alembic.ini
├─ pytest.ini
└─ requirements.txt
```

生产部署应由反向代理或对象存储/CDN 提供最终发布文件，并让 `base_url` 指向真实访问地址；不要假设生产发布目录与 Seed 的本地目录相同。
