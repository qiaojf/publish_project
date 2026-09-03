# 本地全项目联调验收报告

验收日期：2026-09-02  
验收结论：**PASS**。最核心六项验收全部通过，未发现未解决的 P0/P1 问题。

## 验收环境

| 组件 | 实测版本/地址 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite，`http://127.0.0.1:5173` |
| 后端 | FastAPI，`http://127.0.0.1:8000` |
| Python | 3.12.13 |
| Node.js / npm | 24.19.0 / 11.17.0 |
| PostgreSQL | 17.11，`127.0.0.1:5432/content_publish` |
| Alembic | `20260902_0001 (head)` |
| 前端模式 | `VITE_USE_MOCK=false` |

## 执行结果

| 检查项 | 实际结果 |
|---|---|
| PostgreSQL 连接 | PASS，FastAPI 健康检查执行 `SELECT 1` |
| 数据表 | PASS：`users`、`contents`、`review_records`、`publish_targets`、`publish_records`、`operation_logs`、`alembic_version` |
| 数据库约束 | PASS：17 个 CHECK/FK/UNIQUE 约束；14 个 `TIMESTAMPTZ` 列 |
| Migration | PASS：`upgrade head`、`downgrade -1`、再次 `upgrade head` |
| Seed | PASS，连续执行保持幂等；默认 2 个账号、6 个目标 |
| Swagger/OpenAPI | PASS：`/docs` 200；25 个路径模板、34 个 HTTP 操作 |
| 后端测试 | PASS：23 passed，0 failed，0 skipped |
| ESLint | PASS：0 error，0 warning |
| 前端生产构建 | PASS：1753 modules transformed |
| 浏览器联调 | PASS：管理员/员工登录、菜单隔离、403、列表、表单、日志与控制台 |
| 浏览器控制台 | PASS：0 error，0 warning |
| 活体 HTTP 验收 | PASS：完整业务闭环、故障重发、搜索、日志、产物访问 |
| 一键启停 | PASS：启动后两端口健康；停止后 8000/5173 关闭而 5432 保持；再次启动健康 |

## 核心业务验收

| 场景 | 验收证据 | 结果 |
|---|---|---|
| employee 创建并提交 | multipart 上传成功；`draft/unpublished -> pending/unpublished` | PASS |
| admin 驳回 | 保存驳回原因；员工可修改并重新提交 | PASS |
| admin 通过并自动发布 | 审核记录为 `approve`，内容进入 `published` | PASS |
| 本地 `view_url` 可打开 | 访问生成的 `index.html` 返回 200，并包含原始文件链接 | PASS |
| published 内容可搜索 | 发布前检索为 0，发布后精确命中并返回后端 `view_url` | PASS |
| 三类记录完整 | `ReviewRecord` 含 submit/reject/submit/approve；`PublishRecord`、`OperationLog` 可查 | PASS |

## 发布故障与事务验收

验收脚本将发布根目录临时指向一个文件，真实触发目录创建失败：

1. 审核状态保持 `approved`，内容发布状态变为 `failed`。
2. 首次发布记录保存 `failed` 和具体错误原因。
3. 修复发布目标后执行 `republish`，不重复审核。
4. 第二次发布记录保存 `success`，内容变为 `published`，新 `view_url` 可访问。
5. 集成测试在 Publisher 执行期间使用独立数据库 Session 观察到已提交的 `publishing` 内容状态与发布记录，证明两阶段事务边界生效。

## 权限与数据安全

- employee 请求用户、审核、操作日志、发布记录管理接口均返回 403。
- employee 发布目标响应不含 `publish_root` 和 `base_url`。
- employee 只能查看/编辑自己的非锁定内容；待审核内容更新返回 409。
- 未发布内容不进入搜索；已发布内容可被登录用户检索。
- JWT、Argon2 密码哈希、禁用账号校验、上传扩展名与路径安全检查均由后端执行。

## 联调中发现并修复的问题

| 级别 | 问题 | 修复与复验 |
|---|---|---|
| P1 | `127.0.0.1:5173` 不在 CORS 白名单，浏览器预检 400 | 同时允许 localhost 与 127.0.0.1；真实登录复验通过 |
| P1 | 前端发送空 Enum 查询值，发布日志等接口返回 422 | API 层统一 `cleanParams`；发布记录成功/失败均正常显示 |
| P1 | `PublishRecord.status=success` 被错误转换为内容状态 `published` | 独立发布记录状态类型与标签；筛选和页面复验通过 |
| P1 | 审核动作使用旧值 `submitted/approved/rejected` | 对齐为 `submit/approve/reject`；历史记录复验通过 |
| P1 | 删除与状态修改返回类型不一致 | API 适配层对齐真实响应实体/`deleted` 对象 |
| P2 | 真实模式页面仍显示 Mock 文案 | 文案按运行模式动态展示 |

## 已知非阻断项

- Vite 构建提示主包约 1.1 MB，属于性能优化项，不影响 MVP 功能与部署验收。
- 测试运行出现 Starlette 关于未来 `httpx2` 的弃用提示；当前 23 项测试均通过，不影响运行。
- 活体验收会保留带时间戳的本地业务数据和发布产物，便于演示及审计；均位于本地开发库和 `local-data/`。

## 复现命令

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
backend/.venv/Scripts/python.exe -m pytest -q -c backend/pytest.ini
npm run lint
npm run build
backend/.venv/Scripts/python.exe backend/scripts/live_smoke_test.py
```

详细启动步骤见 `docs/LOCAL_DEVELOPMENT.md`，契约核对见 `docs/integration_contract_check.md`。
