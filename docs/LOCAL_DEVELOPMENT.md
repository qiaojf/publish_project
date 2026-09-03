# 本地开发、联调与部署

本项目由根目录 Vue 前端、`backend/` FastAPI 服务、PostgreSQL 和本地发布目录组成。Windows 下可使用脚本启动，也可分别在两个终端运行。

## 环境要求

- Node.js 20.19+（当前验收：24.19.0）
- npm 10+（当前验收：11.17.0）
- Python 3.11+（当前验收：3.12.13）
- PostgreSQL 16+（当前验收：17.11）
- PowerShell 5.1+

当前工作区已经在 `local-data/postgres/pgsql` 配置了便携 PostgreSQL；该目录被 Git 忽略。其他环境可以使用系统安装的 PostgreSQL。

## 首次配置

创建业务库和隔离测试库：

```powershell
createdb -h 127.0.0.1 -U postgres content_publish
createdb -h 127.0.0.1 -U postgres content_publish_test
```

复制环境文件并修改 PostgreSQL 密码与 JWT 密钥：

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item .env.example .env.local
```

真实联调的前端变量：

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

后端关键变量：

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish
TEST_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish_test
SOURCE_STORAGE_ROOT=../local-data/source
PREVIEW_STORAGE_ROOT=../local-data/preview
LOCAL_PUBLISHED_ROOT=../local-data/published
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

安装依赖：

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
npm install
```

## 一键启动

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

脚本会检查/启动当前便携 PostgreSQL（若存在）、执行 Alembic、幂等 Seed，并启动后端与前端。服务地址：

- 前端：`http://127.0.0.1:5173`
- Swagger：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/health`

停止脚本启动的应用进程：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/stop-local.ps1
```

停止脚本不会关闭 PostgreSQL，以免影响其他本地会话。

## 手动启动

数据库迁移和 Seed：

```powershell
Set-Location backend
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe scripts/seed.py
```

终端一，启动 FastAPI：

```powershell
Set-Location backend
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

终端二，启动 Vue：

```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```

## 本地账号

| 角色 | 用户名 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 普通员工 | `employee` | `employee123` |

这些是开发 Seed 账号，部署到共享或生产环境前必须替换默认密码和 JWT 密钥。

## 测试与验收

后端 PostgreSQL 集成测试：

```powershell
Set-Location backend
.venv/Scripts/python.exe -m pytest -q
```

前端检查与生产构建：

```powershell
npm run lint
npm run build
```

前后端已启动后，运行活体服务验收：

```powershell
Set-Location backend
.venv/Scripts/python.exe scripts/live_smoke_test.py
```

该脚本会真实调用 HTTP API，生成独立时间戳数据，并覆盖用户管理、权限、提交、驳回、修改、重提、发布、故障注入、重新发布、搜索、日志、Swagger 和发布 URL。

## 数据与发布产物

- 原始上传：`local-data/source`
- 预览缓存：`local-data/preview`
- 发布产物：`local-data/published`
- 运行日志：`local-data/logs`
- PID 文件：`local-data/run`

本地发布 URL 只在 `APP_ENV=development` 时挂载。生产环境应由 Nginx、对象存储或内部文件服务提供静态内容，不应启用开发静态挂载。

## 常见问题

- `5432` 连接失败：确认 PostgreSQL 已启动、两个数据库已创建且 `.env` 密码正确。
- 浏览器出现 CORS：确认前端使用 `localhost:5173` 或 `127.0.0.1:5173`，并与后端 `CORS_ORIGINS` 一致。
- 列表返回 422：确认调用端没有发送空的 Enum 参数；当前前端已在 `cleanParams` 统一过滤。
- 发布失败：管理员在发布记录查看 `failure_reason`，修复发布目标后执行“重新发布”，无需重复审核。
- 迁移回退验证：执行 `alembic downgrade -1` 后再执行 `alembic upgrade head`；不要在包含重要数据的共享库上随意回退。
