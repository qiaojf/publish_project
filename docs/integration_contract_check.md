# 前后端集成契约检查

检查日期：2026-09-02  
结论：34 个 API 操作已对齐；前端真实 API 模式使用统一响应解包、空查询参数清理与 snake_case 字段。

## API 路径

| 方法与路径 | 前端调用 | 后端路由 | 权限 | 结果 |
|---|---|---|---|---|
| `GET /api/health` | 部署/验收脚本 | `health.py` | 公开 | PASS |
| `POST /api/auth/login` | `src/api/auth.ts` | `auth.py` | 公开 | PASS |
| `POST /api/auth/logout` | `src/api/auth.ts` | `auth.py` | 登录 | PASS |
| `GET /api/auth/me` | `src/api/auth.ts` | `auth.py` | 登录 | PASS |
| `GET /api/users` | `src/api/users.ts` | `users.py` | admin | PASS |
| `POST /api/users` | `src/api/users.ts` | `users.py` | admin | PASS |
| `GET /api/users/{id}` | `src/api/users.ts` | `users.py` | admin | PASS |
| `PUT /api/users/{id}` | `src/api/users.ts` | `users.py` | admin | PASS |
| `PATCH /api/users/{id}/status` | `src/api/users.ts` | `users.py` | admin | PASS |
| `DELETE /api/users/{id}` | `src/api/users.ts` | `users.py` | admin | PASS |
| `GET /api/contents` | `src/api/contents.ts` | `contents.py` | 登录/数据隔离 | PASS |
| `POST /api/contents` | `src/api/contents.ts` | `contents.py` | 登录 | PASS |
| `GET /api/contents/{id}` | `src/api/contents.ts` | `contents.py` | 登录/数据隔离 | PASS |
| `PUT /api/contents/{id}` | `src/api/contents.ts` | `contents.py` | 登录/状态约束 | PASS |
| `DELETE /api/contents/{id}` | `src/api/contents.ts` | `contents.py` | 登录/状态约束 | PASS |
| `POST /api/contents/{id}/submit` | `src/api/contents.ts` | `contents.py` | 创建人或 admin | PASS |
| `POST /api/contents/{id}/publish` | `src/api/contents.ts` | `contents.py` | admin | PASS |
| `POST /api/contents/{id}/republish` | `src/api/contents.ts` | `contents.py` | admin | PASS |
| `GET /api/contents/{id}/preview` | `src/api/contents.ts` | `contents.py` | 登录/数据隔离 | PASS |
| `GET /api/reviews` | `src/api/reviews.ts` | `reviews.py` | admin | PASS |
| `GET /api/reviews/{content_id}` | `src/api/reviews.ts` | `reviews.py` | admin | PASS |
| `POST /api/reviews/{content_id}/approve` | `src/api/reviews.ts` | `reviews.py` | admin | PASS |
| `POST /api/reviews/{content_id}/reject` | `src/api/reviews.ts` | `reviews.py` | admin | PASS |
| `GET /api/publish-targets` | `src/api/publishTargets.ts` | `publish_targets.py` | 登录/按角色脱敏 | PASS |
| `POST /api/publish-targets` | `src/api/publishTargets.ts` | `publish_targets.py` | admin | PASS |
| `GET /api/publish-targets/{id}` | Swagger/API 预留 | `publish_targets.py` | admin | PASS |
| `PUT /api/publish-targets/{id}` | `src/api/publishTargets.ts` | `publish_targets.py` | admin | PASS |
| `PATCH /api/publish-targets/{id}/status` | `src/api/publishTargets.ts` | `publish_targets.py` | admin | PASS |
| `DELETE /api/publish-targets/{id}` | `src/api/publishTargets.ts` | `publish_targets.py` | admin | PASS |
| `GET /api/publish-records` | `src/api/logs.ts` | `publish_records.py` | admin | PASS |
| `GET /api/publish-records/{id}` | Swagger/API 预留 | `publish_records.py` | admin | PASS |
| `GET /api/search` | `src/api/search.ts` | `search.py` | 登录 | PASS |
| `GET /api/logs/operations` | `src/api/logs.ts` | `logs.py` | admin | PASS |
| `GET /api/dashboard` | `src/api/dashboard.ts` | `dashboard.py` | 登录/角色范围 | PASS |

OpenAPI 实测为 25 个路径模板、34 个 HTTP 操作。未由当前页面单独调用的详情接口保留为后台管理 API，并已由 OpenAPI/集成测试检查。

## 字段、状态和类型

- 请求与响应统一使用 `snake_case`；前端领域类型不维护 camelCase 副本。
- `review_status`：`draft | pending | approved | rejected`。
- `publish_status`：`unpublished | publishing | published | failed`。
- `PublishRecord.status`：`publishing | success | failed`，不再错误映射成 `published`。
- `ReviewRecord.action`：`submit | approve | reject`，并包含 `from_status`、`to_status`、`operated_by`。
- 角色仅允许 `admin | employee`；用户状态仅允许 `active | disabled`。
- `content_type` 在 Vue、Pydantic、SQLAlchemy 约束中均为：`html | dynamic | ppt | pdf | word | excel | image | file`。
- 删除接口统一解析 `{ "deleted": true }`；用户/发布目标状态修改接口解析更新后的实体。

## 通用响应、分页和日期

- 成功响应统一为 `{ success, data, message }`，由 `src/api/runtime.ts` 的 `unwrap` 在一处解包。
- 错误响应统一为 `{ success: false, data: null, message }`，401 清理认证并回登录页，403 进入无权限页。
- `users`、`contents`、`reviews`、`publish-records`、`search`、`operation logs` 均使用 `page`、`page_size` 及 `{ items, total, page, page_size }`。
- 前端通过 `cleanParams` 删除空字符串、`undefined` 和 `null` 查询值，避免把空值传给 FastAPI Enum 导致 422。
- 日期筛选统一使用 `date_from`、`date_to`；API 返回 ISO 8601，数据库时间列使用 `TIMESTAMPTZ`，Vue 负责本地显示。

## 认证、权限与敏感字段

- 登录返回 JWT 和当前用户；Axios 统一添加 `Authorization: Bearer`。
- 禁用账号不能登录，账号被禁用后已有 token 也会被拒绝。
- `employee` 无权访问用户、审核、发布配置写操作、操作日志和发布记录管理接口。
- 普通员工只能修改自己的草稿或已驳回内容，待审核内容锁定，已发布内容不可由员工删除。
- 普通员工获取发布目标时不返回 `publish_root` 与 `base_url`；管理员审核页可核对这些字段。
- 搜索接口只返回 `publish_status=published` 内容；访问地址直接使用后端返回的 `view_url`。

## 上传、发布与本地部署

- 内容新增/修改统一使用 `multipart/form-data`；JSON 管理接口保持 `application/json`。
- 发布采用两阶段事务：先提交 `publishing` 内容状态、发布记录和操作日志，再执行文件系统发布，最后提交 `success/published` 或 `failed`。
- 本地发布根目录为 `local-data/published`，仅开发环境挂载 `/local-published`。
- 前端真实模式为 `VITE_USE_MOCK=false`，API 基址为 `http://localhost:8000/api`。
- CORS 同时允许 `http://localhost:5173` 与 `http://127.0.0.1:5173`。

## 联调修复记录

1. 分离内容发布状态与发布记录状态，修正日志筛选和状态标签。
2. 将审核动作从前端旧值 `submitted/approved/rejected` 对齐为 `submit/approve/reject`。
3. 对齐删除、状态修改响应类型和用户更新时间字段。
4. 清理空枚举查询参数，修复真实 API 模式列表/发布日志 422。
5. 修复 `127.0.0.1` 前端来源的 CORS 预检失败。
6. 将登录页和内容表单的运行模式提示改为随 `VITE_USE_MOCK` 变化。
