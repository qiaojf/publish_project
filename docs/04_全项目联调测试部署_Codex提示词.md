# 04_全项目联调测试部署_Codex提示词

# Codex 开发任务：全项目联调、测试与本地部署

你是一名高级全栈工程师与系统集成工程师。精通 Vue 3 + TypeScript 前端开发；精通 Python / FastAPI / PostgreSQL 后端开发，以及精通数据库设计。
当前项目已经分别完成以下三个部分：

1. Vue 3 + TypeScript 前端
2. Python + FastAPI 后端
3. PostgreSQL 数据库

本阶段的任务不是重新设计系统，也不是增加新功能。

本阶段只负责：

```text
前端
+
后端
+
PostgreSQL
↓
契约检查
↓
接口对齐
↓
字段对齐
↓
状态对齐
↓
权限对齐
↓
数据库对齐
↓
本地联调
↓
完整业务测试
↓
修复问题
↓
本地部署
```

当前阶段暂时不考虑生产环境部署。

明确不处理：

```text
Nginx 生产配置
HTTPS
正式域名
systemd
Docker Swarm
Kubernetes
云服务器
正式数据库账号
正式备份方案
生产环境安全加固
生产监控
CI/CD
```

目标是：

```text
在一台本地开发电脑上，
让 Vue + FastAPI + PostgreSQL 完整跑起来，
并验证业务闭环没有问题。
```

---

# 一、执行前必须阅读的资料

请先检查项目中的以下需求和开发资料：

```text
01_功能说明.md
02_前端页面.md
03_后端API.md
04_数据库设计.md
```

以及已经完成的：

```text
前端开发代码
后端开发代码
PostgreSQL ORM / Alembic
README
.env.example
```

如果存在之前用于 Codex 开发的提示词，也可以参考，但最终以：

```text
实际需求文档
+
当前代码
```

为准。

---

# 二、本阶段最高原则

## 原则 1：不要重新设计系统

禁止：

```text
重新规划页面
重新规划数据库
重写整个前端
重写整个后端
增加新的角色系统
增加复杂权限
增加新工作流
改变核心业务流程
```

只允许进行：

```text
修复
对齐
补漏
联调
测试
本地运行配置
```

---

## 原则 2：优先最小修改

如果前端和后端只有：

```text
字段名
API 路径
状态值
Response 结构
参数格式
```

不一致：

优先修改最少的一侧。

不要为了一个字段名不一致重构整个模块。

---

## 原则 3：以业务流程正确为最终标准

最终必须保证：

```text
管理员创建用户
↓
普通员工登录
↓
创建 / 上传内容
↓
保存草稿
↓
提交审核
↓
管理员审核
↓
驳回
↓
员工修改重新提交
↓
管理员审核通过
↓
自动发布
↓
生成 URL
↓
员工检索
↓
打开发布内容
↓
日志完整
```

---

# 三、最终本地项目结构

优先整理成：

```text
content-publish-platform/
│
├─ frontend/
│
├─ backend/
│
├─ docs/
│
│  ├─ 01_功能说明.md
│  ├─ 02_前端页面.md
│  ├─ 03_后端API.md
│  └─ 04_数据库设计.md
│
└─ README.md
```

数据库代码主要应保留在：

```text
backend/app/db/
backend/alembic/
```

不要为了“分层”强制创建独立 database 项目。

---

# 四、第一阶段：检查三个项目当前状态

首先检查：

## Frontend

确认：

```text
Vue 3
TypeScript
Vite
Vue Router
Pinia
Axios
Element Plus
```

并检查：

```text
package.json
src/api/
src/pages/
src/router/
src/stores/
.env
.env.example
```

---

## Backend

确认：

```text
FastAPI
Pydantic v2
SQLAlchemy 2.x
Alembic
psycopg
JWT
pytest
```

并检查：

```text
app/main.py
app/api/
app/services/
app/repositories/
app/db/
app/publishers/
alembic/
requirements.txt 或 pyproject.toml
.env.example
```

---

## PostgreSQL

确认代码固定使用：

```text
PostgreSQL
```

不能再存在：

```text
SQLite fallback
sqlite:///...
MySQL 配置
```

如果发现之前遗留的 SQLite 兼容逻辑：

```text
删除或修正
```

确保：

```text
DATABASE_URL=postgresql+psycopg://...
```

---

# 五、第二阶段：建立集成契约检查表

在实际联调前，先生成一个内部检查文件：

```text
docs/integration_contract_check.md
```

至少检查以下内容。

---

# 六、API 路径对齐

前端调用与后端实际 FastAPI Router 必须逐一核对。

最终至少应存在：

```text
GET    /api/health

POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/users
POST   /api/users
GET    /api/users/{id}
PUT    /api/users/{id}
PATCH  /api/users/{id}/status
DELETE /api/users/{id}

GET    /api/contents
POST   /api/contents
GET    /api/contents/{id}
PUT    /api/contents/{id}
DELETE /api/contents/{id}
POST   /api/contents/{id}/submit
POST   /api/contents/{id}/publish
POST   /api/contents/{id}/republish
GET    /api/contents/{id}/preview

GET    /api/reviews
GET    /api/reviews/{content_id}
POST   /api/reviews/{content_id}/approve
POST   /api/reviews/{content_id}/reject

GET    /api/publish-targets
POST   /api/publish-targets
GET    /api/publish-targets/{id}
PUT    /api/publish-targets/{id}
PATCH  /api/publish-targets/{id}/status
DELETE /api/publish-targets/{id}

GET    /api/publish-records
GET    /api/publish-records/{id}

GET    /api/search

GET    /api/logs/operations

GET    /api/dashboard
```

检查：

```text
前端 API 文件实际调用路径
后端 FastAPI 实际 Router 路径
```

必须完全一致。

---

# 七、字段名称对齐

统一使用后端 JSON 的：

```text
snake_case
```

建议前端 TypeScript 直接使用相同字段。

例如 Content：

```json
{
  "id": 1001,
  "title": "BIM Proposal",
  "description": "...",
  "category": "proposal",
  "content_type": "ppt",
  "review_status": "pending",
  "publish_status": "unpublished",
  "publish_target_id": 2,
  "view_url": null,
  "created_by": 2,
  "created_at": "...",
  "updated_at": "..."
}
```

检查并修复类似：

```text
contentType
reviewStatus
publishStatus
publishTargetId
```

与：

```text
content_type
review_status
publish_status
publish_target_id
```

不一致的问题。

除非项目已经有统一可靠的转换层，否则不要同时维护两种字段命名。

---

# 八、统一状态值

三部分必须完全一致。

## review_status

```text
draft
pending
approved
rejected
```

## publish_status

```text
unpublished
publishing
published
failed
```

## PublishRecord.status

```text
publishing
success
failed
```

注意：

```text
Content.publish_status
```

与：

```text
PublishRecord.status
```

不是同一个状态集合。

禁止错误混用：

```text
Content.publish_status = success
```

正确：

```text
Content.publish_status = published
```

---

# 九、角色对齐

全项目只能使用：

```text
admin
employee
```

检查并删除 / 修复：

```text
administrator
staff
normal_user
user
superadmin
```

等不一致值。

---

# 十、统一用户状态

只允许：

```text
active
disabled
```

---

# 十一、统一 ContentType

最终：

```text
html
dynamic
ppt
pdf
word
excel
image
file
```

前端 Select、TypeScript Type、Pydantic Enum、SQLAlchemy Check Constraint 必须一致。

---

# 十二、统一 API Response

检查后端实际返回与前端 Axios 解析逻辑。

统一成功格式：

```json
{
  "success": true,
  "data": {},
  "message": ""
}
```

错误：

```json
{
  "success": false,
  "data": null,
  "message": "错误说明"
}
```

前端不能一部分代码使用：

```text
response.data.data
```

另一部分直接认为：

```text
response.data
```

就是业务数据。

统一 Axios 层处理。

---

# 十三、分页契约

列表统一 Request：

```text
page
page_size
```

例如：

```text
?page=1&page_size=20
```

Response：

```json
{
  "success": true,
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  },
  "message": ""
}
```

检查：

```text
users
contents
reviews
publish-records
search
operation logs
```

全部一致。

---

# 十四、日期参数对齐

统一：

```text
date_from
date_to
```

API 返回时间：

```text
ISO 8601
```

数据库：

```text
TIMESTAMPTZ
```

前端负责显示本地时间。

---

# 十五、认证契约对齐

前端登录：

```text
POST /api/auth/login
```

Request：

```json
{
  "username": "employee",
  "password": "employee123"
}
```

Response：

```json
{
  "success": true,
  "data": {
    "token": "...",
    "user": {
      "id": 2,
      "username": "employee",
      "name": "Employee",
      "role": "employee",
      "status": "active"
    }
  },
  "message": ""
}
```

Axios：

```text
Authorization: Bearer {token}
```

检查：

```text
401
→ 清理登录状态
→ /login

403
→ 权限提示或 /403
```

---

# 十六、Mock 模式处理

前端之前可能实现：

```text
VITE_USE_MOCK=true
```

正式开始本地联调时必须：

```env
VITE_USE_MOCK=false
```

不要删除 Mock 功能。

但本地真实联调时：

```text
必须调用 FastAPI
```

避免出现：

```text
页面看起来正常
但实际一直使用 Mock 数据
```

---

# 十七、第三阶段：PostgreSQL 本地环境

准备本地 PostgreSQL。

数据库：

```text
content_publish
```

测试数据库：

```text
content_publish_test
```

例如：

```sql
CREATE DATABASE content_publish;
CREATE DATABASE content_publish_test;
```

如果本地 PostgreSQL 已有：

```text
不要重复安装
```

只确认：

```text
连接地址
数据库
用户
密码
端口
```

---

# 十八、Backend 本地 .env

创建本地：

```text
backend/.env
```

基于：

```text
.env.example
```

例如：

```env
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish

TEST_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish_test

JWT_SECRET_KEY=local-development-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

SOURCE_STORAGE_ROOT=./storage/source
PREVIEW_STORAGE_ROOT=./storage/preview

MAX_UPLOAD_SIZE_MB=100

CORS_ORIGINS=http://localhost:5173
```

不要将真实 `.env` 提交 Git。

---

# 十九、执行 Alembic

进入 backend：

```bash
alembic upgrade head
```

必须成功。

检查 PostgreSQL 中存在：

```text
users
contents
publish_targets
review_records
publish_records
operation_logs
alembic_version
```

如果 Migration 与 ORM 不一致：

```text
修复 Migration / Model
```

不要直接手改数据库绕过去。

---

# 二十、运行 Seed

执行：

```bash
python scripts/seed.py
```

确认：

```text
admin
employee
```

存在。

开发账号：

```text
admin / admin123

employee / employee123
```

同时确认开发 PublishTarget 存在。

Seed 必须幂等。

重复运行不能重复创建数据。

---

# 二十一、第四阶段：先独立验证 FastAPI

不要一开始就启动 Vue 联调。

先启动后端：

```bash
uvicorn app.main:app --reload --port 8000
```

确认：

```text
http://localhost:8000/docs
```

和：

```text
GET http://localhost:8000/api/health
```

正常。

---

# 二十二、Swagger 后端验收顺序

通过 Swagger / curl / httpx 按顺序测试。

## 1. Health

```text
GET /api/health
```

---

## 2. Admin 登录

```text
POST /api/auth/login
```

---

## 3. Employee 登录

```text
POST /api/auth/login
```

---

## 4. Admin 创建用户

```text
POST /api/users
```

---

## 5. Employee 创建内容

```text
POST /api/contents
```

---

## 6. Employee 提交

```text
POST /api/contents/{id}/submit
```

---

## 7. Admin 查看审核

```text
GET /api/reviews
```

---

## 8. Admin 驳回

```text
POST /api/reviews/{id}/reject
```

---

## 9. Employee 修改

```text
PUT /api/contents/{id}
```

---

## 10. Employee 重新提交

```text
POST /api/contents/{id}/submit
```

---

## 11. Admin 通过

```text
POST /api/reviews/{id}/approve
```

---

## 12. 查看发布状态

```text
GET /api/contents/{id}
```

---

## 13. Search

```text
GET /api/search
```

---

## 14. Publish Records

```text
GET /api/publish-records
```

---

## 15. Operation Logs

```text
GET /api/logs/operations
```

如果这一阶段未通过：

```text
不要开始 Vue 联调
```

先修后端。

---

# 二十三、第五阶段：数据库联动检查

每个关键操作都同时检查 PostgreSQL。

---

# 二十四、创建内容检查

employee 创建后：

```text
contents
```

必须：

```text
review_status = draft

publish_status = unpublished

created_by = 当前 employee
```

---

# 二十五、提交审核检查

提交后：

```text
contents.review_status = pending
```

同时：

```text
review_records.action = submit
```

以及：

```text
operation_logs.action = submit_content
```

---

# 二十六、审核驳回检查

管理员 reject：

```text
contents.review_status = rejected

reject_reason != null
```

新增：

```text
review_records.action = reject
```

以及：

```text
operation_logs.action = reject_content
```

---

# 二十七、重新提交检查

审核历史应该至少：

```text
submit
reject
submit
```

不能覆盖旧记录。

---

# 二十八、审核通过检查

首先：

```text
review_status = approved

publish_status = publishing
```

然后成功时：

```text
publish_status = published

view_url != null

published_at != null
```

同时：

```text
review_records.action = approve
```

和：

```text
publish_records.status = success
```

---

# 二十九、发布失败检查

必须专门制造一次失败。

可以采用：

```text
测试 Publisher 抛异常
```

或者：

```text
配置一个无效本地 publish_root
```

不要破坏开发电脑系统目录。

预期：

```text
review_status = approved

publish_status = failed
```

以及：

```text
publish_records.status = failed

error_message != null
```

---

# 三十、重新发布检查

修复发布目标后执行：

```text
POST /api/contents/{id}/republish
```

数据库：

```text
PublishRecord #1 = failed

PublishRecord #2 = success
```

两条都必须保留。

---

# 三十一、第六阶段：本地发布目录方案

本地开发不要使用：

```text
/data/...
/var/www/...
```

这类生产路径。

统一创建项目内或项目旁边的本地目录。

建议：

```text
local-data/
├─ source/
├─ preview/
└─ published/
   ├─ html/
   ├─ ppt/
   ├─ pdf/
   ├─ documents/
   ├─ images/
   └─ files/
```

例如：

```text
content-publish-platform/
├─ frontend/
├─ backend/
└─ local-data/
   └─ published/
```

---

# 三十二、本地 PublishTarget 示例

例如：

## HTML

```text
publish_root:
../local-data/published/html/

base_url:
http://localhost:8000/local-published/html/
```

## PPT

```text
publish_root:
../local-data/published/ppt/

base_url:
http://localhost:8000/local-published/ppt/
```

## PDF

```text
publish_root:
../local-data/published/pdf/

base_url:
http://localhost:8000/local-published/pdf/
```

---

# 三十三、本地发布内容访问

为了本地联调，不需要 Nginx。

允许 FastAPI 临时挂载：

```text
local-data/published/
```

例如使用：

```python
StaticFiles
```

挂载：

```text
/local-published
```

这样：

```text
http://localhost:8000/local-published/ppt/1001-demo/
```

可以直接访问。

注意：

这只是：

```text
本地开发方案
```

不要因此重构 PublishTarget 设计。

生产环境未来可以替换访问层。

---

# 三十四、FastAPI StaticFiles 要求

如果项目目前没有本地静态发布访问：

可以增加：

```text
仅 development 环境启用
```

例如：

```text
APP_ENV=development
```

时挂载。

生产逻辑暂不处理。

不要把发布根目录完全写死在代码中。

---

# 三十五、第七阶段：启动 Vue 真实联调

前端 `.env.local` 或 `.env.development`：

```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

启动：

```bash
npm install
npm run dev
```

默认：

```text
http://localhost:5173
```

---

# 三十六、检查浏览器 Network

联调时必须检查 DevTools：

```text
Network
Console
```

确保：

```text
请求真正访问 localhost:8000/api
```

不能出现：

```text
Mock API
假数据
请求未发送
```

---

# 三十七、第八阶段：Vue + FastAPI 完整联调

必须按真实业务顺序测试。

---

# 三十八、场景 A：管理员登录

打开：

```text
http://localhost:5173/login
```

使用：

```text
admin / admin123
```

检查：

```text
登录成功
JWT 保存正确
GET /api/auth/me 成功
管理员菜单正确
```

菜单至少：

```text
首页
内容管理
审核管理
内容检索
用户管理
发布配置
日志
```

---

# 三十九、场景 B：普通员工登录

```text
employee / employee123
```

确认菜单：

```text
首页
我的内容
内容检索
```

不能显示：

```text
审核管理
用户管理
发布配置
日志
```

---

# 四十、场景 C：普通员工创建 PPT 内容

employee：

```text
新建内容
↓
content_type = ppt
↓
上传 .pptx
↓
选择 PPT 发布区
↓
保存草稿
```

检查：

```text
UI 显示 draft
PostgreSQL draft
```

---

# 四十一、场景 D：员工提交发布

点击：

```text
提交发布
```

确认：

```text
POST /api/contents/{id}/submit
```

之后：

```text
状态 = 待审核
```

同时：

```text
普通员工不能继续编辑 pending 内容
```

---

# 四十二、场景 E：管理员看到待审核

admin：

```text
审核管理
```

必须看到刚才内容。

打开详情：

```text
内容
创建人
文件
发布目标
审核历史
```

正确。

---

# 四十三、场景 F：管理员驳回

填写：

```text
请修改标题
```

点击：

```text
驳回
```

employee 再登录后：

```text
看到已驳回
看到 reject_reason
可以编辑
```

---

# 四十四、场景 G：员工重新提交

员工：

```text
编辑
↓
保存
↓
重新提交
```

管理员再次：

```text
看到 pending
```

---

# 四十五、场景 H：管理员审核通过

admin：

```text
审核通过并发布
```

确认：

```text
review_status = approved
```

发布过程：

```text
publishing
```

最终：

```text
published
```

或者失败：

```text
failed
```

前端必须正确显示。

---

# 四十六、场景 I：打开发布内容

发布成功后：

前端使用：

```text
view_url
```

点击：

```text
打开内容
```

必须可以访问本地 FastAPI StaticFiles 中的已发布页面。

前端不能自行拼接 URL。

---

# 四十七、场景 J：搜索

employee：

```text
内容检索
```

搜索刚才发布内容。

必须出现。

点击：

```text
打开内容
```

正常。

---

# 四十八、第九阶段：权限专项测试

除了 UI，还必须直接测试 API。

---

# 四十九、Employee 调用户管理

```text
GET /api/users
```

必须：

```text
403
```

---

# 五十、Employee 调审核

```text
GET /api/reviews
```

必须：

```text
403
```

---

# 五十一、Employee 调日志

```text
GET /api/logs/operations
```

必须：

```text
403
```

---

# 五十二、Employee 修改 PublishTarget

```text
POST /api/publish-targets
```

必须：

```text
403
```

---

# 五十三、Employee 读取 PublishTarget

```text
GET /api/publish-targets
```

允许。

但是 Response 绝不能包含：

```text
publish_root
```

---

# 五十四、Employee 修改别人内容

必须：

```text
403
```

---

# 五十五、Employee 修改 pending 内容

必须：

```text
拒绝
```

---

# 五十六、第十阶段：搜索专项测试

数据库准备不同状态内容：

```text
draft
pending
rejected
published
failed
```

调用：

```text
GET /api/search
```

只能返回：

```text
published
```

前端 Search 页面也只能显示：

```text
published
```

---

# 五十七、第十一阶段：日志专项测试

检查关键操作。

至少应该看到：

```text
login
create_content
update_content
submit_content
reject_content
approve_content
publish_content
republish_content
```

发布日志：

```text
publish_records
```

至少包含：

```text
publishing
success / failed
publish_url
error_message
started_at
finished_at
```

---

# 五十八、第十二阶段：前端构建检查

执行：

```bash
npm run build
```

必须：

```text
无 TypeScript Error
Build 成功
```

如果有：

```text
unused
type mismatch
API type mismatch
```

修复。

---

# 五十九、后端测试

执行：

```bash
pytest
```

必须通过。

重点：

```text
认证
权限
内容权限
状态流转
审核
发布成功
发布失败
重新发布
搜索
发布目录信息隐藏
数据库约束
```

---

# 六十、Alembic 可逆测试

至少执行一次：

```bash
alembic downgrade -1
```

然后：

```bash
alembic upgrade head
```

确认 Migration 正常。

测试前：

```text
确认只对本地开发数据库操作
```

不要误操作其他数据库。

---

# 六十一、第十三阶段：增加简单 API 集成测试

如果当前项目测试不足：

补充：

```text
tests/integration/
```

至少完成：

```text
test_auth_flow.py
test_content_flow.py
test_review_flow.py
test_publish_flow.py
test_permissions.py
test_search.py
```

核心测试重点不是覆盖率数字。

重点是：

```text
完整业务链条
```

---

# 六十二、可选：简单 E2E

如果当前项目已经有 Playwright：

可以补充。

如果没有：

```text
本阶段不强制安装
```

不要因为 E2E 工具增加大量额外工作。

人工业务验收 + API integration test 足够第一阶段。

---

# 六十三、第十四阶段：本地一键启动辅助

为了方便以后本地运行，可以增加简单脚本。

Windows 可以：

```text
scripts/start-local.ps1
```

Linux / macOS 可以：

```text
scripts/start-local.sh
```

但不要做复杂进程管理。

脚本可以提示：

```text
1. PostgreSQL 是否运行
2. backend .env 是否存在
3. alembic upgrade head
4. 启动 FastAPI
5. 启动 Vue
```

如果无法可靠同时管理两个前台进程：

```text
不要硬做复杂脚本
```

README 写清楚两个终端启动即可。

---

# 六十四、推荐本地启动方式

## Terminal 1

PostgreSQL：

```text
确认本地 PostgreSQL 服务运行
```

---

## Terminal 2

```bash
cd backend

alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

---

## Terminal 3

```bash
cd frontend

npm install

npm run dev
```

访问：

```text
Frontend:
http://localhost:5173

Backend:
http://localhost:8000

Swagger:
http://localhost:8000/docs
```

---

# 六十五、第十五阶段：生成本地联调 README

更新根目录：

```text
README.md
```

或者增加：

```text
docs/LOCAL_DEVELOPMENT.md
```

必须说明：

```text
1. PostgreSQL 安装要求
2. 创建 content_publish
3. 创建 content_publish_test
4. backend .env
5. frontend .env
6. 安装 Python 依赖
7. 安装 npm 依赖
8. alembic upgrade head
9. seed
10. 启动 FastAPI
11. 启动 Vue
12. admin / employee 测试账号
13. 本地 PublishTarget
14. 本地发布目录
15. 本地 view_url 规则
16. pytest
17. npm run build
18. 常见错误
```

---

# 六十六、常见错误必须检查

至少检查以下问题。

## CORS

如果浏览器报：

```text
CORS
```

检查：

```env
CORS_ORIGINS=http://localhost:5173
```

---

## PostgreSQL 连接失败

检查：

```text
PostgreSQL 服务
DATABASE_URL
用户名
密码
数据库名
端口
```

---

## 401

检查：

```text
Token
Authorization Header
JWT Secret
Token Expiration
```

---

## 403

确认：

```text
当前用户 role
资源 owner
用户 status
```

---

## 上传 422

检查：

```text
multipart/form-data
字段名称
file 参数
content_type
```

---

## PublishTarget 不匹配

检查：

```text
content_type
content_types JSONB
```

---

## 发布成功但页面打不开

检查：

```text
publish_root
base_url
relative_path
StaticFiles mount
index.html
```

---

## 前端看起来正常但数据库没有数据

优先检查：

```text
VITE_USE_MOCK
```

必须是：

```text
false
```

---

# 六十七、第十六阶段：生成验收报告

最终生成：

```text
docs/LOCAL_INTEGRATION_TEST_REPORT.md
```

报告不要只写：

```text
测试通过
```

至少包含：

```text
环境
前端版本
后端版本
PostgreSQL 版本
数据库 Migration 状态
测试账号

API 契约检查
数据库检查
权限测试
业务流程测试
发布成功测试
发布失败测试
重新发布测试
搜索测试
日志测试
前端 Build
pytest

发现的问题
已修复的问题
仍未解决的问题
```

---

# 六十八、验收表

至少生成如下结果。

| 分类 | 项目 | 结果 |
|---|---|---|
| 环境 | PostgreSQL 连接 | PASS / FAIL |
| 环境 | Alembic | PASS / FAIL |
| 环境 | FastAPI 启动 | PASS / FAIL |
| 环境 | Vue 启动 | PASS / FAIL |
| 认证 | admin 登录 | PASS / FAIL |
| 认证 | employee 登录 | PASS / FAIL |
| 用户 | admin 创建用户 | PASS / FAIL |
| 权限 | employee 禁止用户管理 | PASS / FAIL |
| 内容 | 创建草稿 | PASS / FAIL |
| 内容 | 上传文件 | PASS / FAIL |
| 审核 | employee submit | PASS / FAIL |
| 审核 | admin reject | PASS / FAIL |
| 审核 | employee resubmit | PASS / FAIL |
| 审核 | admin approve | PASS / FAIL |
| 发布 | publishing 状态 | PASS / FAIL |
| 发布 | success | PASS / FAIL |
| 发布 | failed | PASS / FAIL |
| 发布 | republish | PASS / FAIL |
| 发布 | view_url | PASS / FAIL |
| 搜索 | 只显示 published | PASS / FAIL |
| 日志 | operation logs | PASS / FAIL |
| 日志 | publish records | PASS / FAIL |
| 安全 | employee 不见 publish_root | PASS / FAIL |
| Build | Vue build | PASS / FAIL |
| Test | pytest | PASS / FAIL |

---

# 六十九、发现 Bug 时的修复原则

按优先级：

```text
P0
数据错误
权限漏洞
发布目录安全问题
状态流转错误

P1
API 对不上
前端无法操作
发布失败
数据库事务问题

P2
页面状态显示错误
错误提示不清楚
筛选问题

P3
样式
间距
非关键体验
```

优先修：

```text
P0
P1
```

---

# 七十、不允许为了通过测试做的事情

禁止：

```text
关闭权限检查

把 employee 改成 admin

绕过数据库约束

硬编码返回成功

把 publish_status 强行写 published

删除失败历史

Mock 代替真实后端

前端自己伪造 view_url

关闭文件路径安全检查
```

测试必须验证真实系统。

---

# 七十一、本阶段最终成功标准

本地环境必须满足：

```text
PostgreSQL
正常运行

FastAPI
正常运行

Vue
正常运行

前端调用真实 API

员工能创建内容

员工能提交审核

管理员能驳回

员工能修改重新提交

管理员能审核通过

后端能自动发布

本地 view_url 可访问

发布失败有正确状态

管理员可以重新发布

搜索只能看到已发布内容

操作日志完整

发布日志完整

权限正确

普通员工看不到服务器物理路径
```

---

# 七十二、最核心的六项验收

最终只要以下六条中任何一条失败：

```text
本阶段不得标记完成
```

六项：

```text
① employee 可以创建并提交内容

② admin 可以审核、驳回、通过

③ approve 后后端能按 PublishTarget 自动发布

④ 发布成功后 view_url 可以在本地打开

⑤ published 内容可以通过搜索找到

⑥ ReviewRecord / PublishRecord / OperationLog 正确保存全过程
```

---

# 七十三、Codex 执行要求

必须实际执行，不要只给建议。

要求：

```text
1. 检查 frontend / backend / PostgreSQL 实现。

2. 建立 integration contract 检查。

3. 修复前后端 API 不一致。

4. 修复字段和状态不一致。

5. 修复数据库 ORM / Migration 不一致。

6. 实际运行 PostgreSQL。

7. 实际执行 alembic upgrade head。

8. 实际运行 seed。

9. 实际启动 FastAPI。

10. 实际检查 Swagger。

11. 实际运行 pytest。

12. 实际启动 Vue。

13. 实际关闭 Mock 模式。

14. 实际完成前后端联调。

15. 实际检查本地发布文件。

16. 实际访问 view_url。

17. 实际运行 npm run build。

18. 修复所有 P0 / P1 问题。

19. 生成 LOCAL_DEVELOPMENT 文档。

20. 生成 LOCAL_INTEGRATION_TEST_REPORT.md。
```

---

# 七十四、停止条件

只有满足以下条件才可以结束任务：

```text
前端可运行
+
后端可运行
+
PostgreSQL 可连接
+
Migration 正常
+
完整业务闭环正常
+
本地自动发布正常
+
核心测试全部 PASS
```

如果仍有未完成问题：

```text
必须在最终报告中明确列出
```

不要把：

```text
未验证
```

写成：

```text
已通过
```

---

# 七十五、最终原则

本阶段本质上是：

```text
Integration
+
Testing
+
Local Deployment
```

不是：

```text
New Feature Development
```

始终保持：

```text
不扩需求

不重新设计

不增加复杂基础设施

优先修复契约问题

优先保证业务闭环

优先保证权限和数据安全

优先保证真实 PostgreSQL + FastAPI + Vue 联调成功
```

最终结果必须是一个可以在本地真实运行并完整演示的公司内部内容自动发布平台 MVP。
