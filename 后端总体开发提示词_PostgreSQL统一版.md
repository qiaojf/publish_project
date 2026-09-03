# Codex 开发任务：公司内部内容自动发布平台后端（PostgreSQL 统一版）

你是一名高级 Python / FastAPI / PostgreSQL 后端工程师。

请根据当前项目中的以下需求文档，实现“公司内部内容自动发布平台”的后端：

- `01_功能说明.md`
- `03_后端API.md`
- `04_数据库设计.md`

其中：

- `01_功能说明.md`：定义业务范围和业务流程。
- `03_后端API.md`：定义 REST API 范围和前后端交互。
- `04_数据库设计.md`：定义 PostgreSQL 数据结构、表关系和数据库约束。

如果三个文件之间存在细节冲突：

1. 业务流程以 `01_功能说明.md` 为准。
2. API 路径与接口职责以 `03_后端API.md` 为准。
3. 数据库实现以 `04_数据库设计.md` 为准。
4. 本提示词中明确指定的技术方案优先于之前任何 SQLite / 多数据库兼容方案。

---

# 一、项目目标

实现一个公司内部使用的“内容自动发布平台”后端。

前端技术已经确定：

```text
Vue 3 + TypeScript
```

后端技术固定：

```text
Python 3.12+
FastAPI
Pydantic v2
SQLAlchemy 2.x
PostgreSQL
psycopg 3
Alembic
JWT
pytest
```

系统只存在两个角色：

```text
admin       管理员
employee    普通员工
```

核心业务闭环：

```text
管理员创建用户
        ↓
普通员工登录
        ↓
创建 / 上传内容
        ↓
保存草稿
        ↓
提交发布申请
        ↓
review_status = pending
        ↓
管理员审核
   ├──────────────┐
   │              │
 驳回            通过
   │              │
   ↓              ↓
rejected       approved
   │              ↓
员工修改       创建发布任务
重新提交           ↓
              内容类型处理
                   ↓
              获取发布目标
                   ↓
              发布到目标目录
                   ↓
              生成 view_url
                   ↓
        published / failed
                   ↓
              员工检索查看
                   ↓
            操作日志 / 发布日志
```

---

# 二、本阶段开发范围

必须实现：

```text
1. 登录 / JWT 认证
2. 两种角色权限
3. 用户管理
4. 内容管理
5. 文件上传
6. 内容提交审核
7. 管理员审核
8. 自动发布
9. 可配置发布目标 / 发布目录
10. 重新发布
11. 内容预览
12. 内容检索
13. Dashboard
14. 操作日志
15. 发布日志
16. PostgreSQL 数据库
17. Alembic Migration
18. Seed 开发数据
19. pytest 核心业务测试
20. Swagger / OpenAPI
```

本阶段明确不实现：

```text
多级审批
复杂 RBAC
部门组织架构
标签
版本管理
发布回滚
定时发布
定时下架
消息通知
评论
收藏
点赞
全文搜索引擎
Elasticsearch
OpenSearch
Redis
Celery
RabbitMQ
Kafka
微服务
Kubernetes
AI 内容分析
工作流设计器
```

保持 MVP。

---

# 三、数据库方案：固定 PostgreSQL

本项目数据库唯一正式方案：

```text
PostgreSQL
```

不要实现：

```text
SQLite
MySQL
MariaDB
```

不要保留“SQLite 开发 / PostgreSQL 生产”的双数据库兼容逻辑。

数据库连接统一通过：

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/content_publish
```

测试数据库：

```env
TEST_DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/content_publish_test
```

数据库驱动：

```text
psycopg 3
```

SQLAlchemy URL：

```text
postgresql+psycopg://
```

---

# 四、推荐项目目录

建议后端独立放在：

```text
backend/
```

目录结构：

```text
backend/
├─ app/
│  ├─ main.py
│  │
│  ├─ api/
│  │  ├─ deps.py
│  │  └─ routes/
│  │     ├─ health.py
│  │     ├─ auth.py
│  │     ├─ users.py
│  │     ├─ contents.py
│  │     ├─ reviews.py
│  │     ├─ publish_targets.py
│  │     ├─ publish_records.py
│  │     ├─ search.py
│  │     ├─ logs.py
│  │     └─ dashboard.py
│  │
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ security.py
│  │  ├─ exceptions.py
│  │  └─ constants.py
│  │
│  ├─ db/
│  │  ├─ base.py
│  │  ├─ session.py
│  │  └─ models/
│  │     ├─ user.py
│  │     ├─ content.py
│  │     ├─ publish_target.py
│  │     ├─ review_record.py
│  │     ├─ publish_record.py
│  │     └─ operation_log.py
│  │
│  ├─ schemas/
│  │  ├─ common.py
│  │  ├─ auth.py
│  │  ├─ user.py
│  │  ├─ content.py
│  │  ├─ review.py
│  │  ├─ publish_target.py
│  │  ├─ publish_record.py
│  │  └─ dashboard.py
│  │
│  ├─ repositories/
│  │  ├─ user_repository.py
│  │  ├─ content_repository.py
│  │  ├─ publish_target_repository.py
│  │  ├─ review_repository.py
│  │  ├─ publish_record_repository.py
│  │  └─ operation_log_repository.py
│  │
│  ├─ services/
│  │  ├─ auth_service.py
│  │  ├─ user_service.py
│  │  ├─ content_service.py
│  │  ├─ review_service.py
│  │  ├─ publish_service.py
│  │  ├─ publish_target_service.py
│  │  ├─ search_service.py
│  │  ├─ dashboard_service.py
│  │  └─ log_service.py
│  │
│  ├─ publishers/
│  │  ├─ base.py
│  │  ├─ factory.py
│  │  ├─ html.py
│  │  ├─ dynamic.py
│  │  ├─ ppt.py
│  │  ├─ pdf.py
│  │  ├─ word.py
│  │  ├─ excel.py
│  │  ├─ image.py
│  │  └─ file.py
│  │
│  └─ utils/
│     ├─ files.py
│     ├─ paths.py
│     ├─ slug.py
│     └─ datetime.py
│
├─ alembic/
│  ├─ env.py
│  └─ versions/
│
├─ scripts/
│  └─ seed.py
│
├─ tests/
│
├─ storage/
│  ├─ source/
│  └─ preview/
│
├─ .env.example
├─ .gitignore
├─ alembic.ini
├─ requirements.txt
└─ README.md
```

如果当前项目已经存在 FastAPI 结构：

```text
在现有项目基础上修改
```

不要无故重新初始化。

---

# 五、后端分层原则

严格保持：

```text
Router
  ↓
Service
  ↓
Repository
  ↓
SQLAlchemy
  ↓
PostgreSQL
```

发布流程：

```text
Router
  ↓
ReviewService / ContentService
  ↓
PublishService
  ↓
PublisherFactory
  ↓
具体 Publisher
  ↓
Filesystem
```

禁止：

```text
Router 直接写 SQL
Router 直接 shutil.copy
Router 直接拼发布路径
```

---

# 六、配置管理

使用：

```text
pydantic-settings
```

建立：

```text
app/core/config.py
```

`.env.example` 至少：

```env
APP_NAME=Internal Content Publish Platform
APP_ENV=development
DEBUG=true

DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish
TEST_DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/content_publish_test

JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

SOURCE_STORAGE_ROOT=./storage/source
PREVIEW_STORAGE_ROOT=./storage/preview

MAX_UPLOAD_SIZE_MB=100

CORS_ORIGINS=http://localhost:5173

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

`.env` 必须：

```text
加入 .gitignore
```

真实数据库密码、JWT Secret 不允许写入 Git。

---

# 七、SQLAlchemy 使用方式

本阶段推荐：

```text
SQLAlchemy 2.x Sync Session
```

使用：

```text
create_engine
sessionmaker
Session
```

数据库驱动：

```text
psycopg 3
```

除非当前项目已经明确使用 AsyncSession，否则不要为了所谓现代化强行改成 async 数据库层。

FastAPI 路由可以正常配合同步 SQLAlchemy 使用。

---

# 八、PostgreSQL 数据字段标准

主键：

```text
BIGINT
```

推荐：

```text
BIGINT GENERATED BY DEFAULT AS IDENTITY
```

SQLAlchemy 可使用：

```text
BigInteger
Identity()
```

时间：

```text
TIMESTAMP WITH TIME ZONE
```

SQLAlchemy：

```python
DateTime(timezone=True)
```

统一保存 UTC。

生成时间：

```python
datetime.now(timezone.utc)
```

不要使用 naive datetime。

---

# 九、数据库核心表

第一阶段固定 6 张表：

```text
users
contents
publish_targets
review_records
publish_records
operation_logs
```

不要新增：

```text
roles
permissions
departments
categories
tags
versions
workflows
notifications
tasks
```

---

# 十、枚举与状态常量

建议在：

```text
app/core/constants.py
```

定义 Python Enum。

## UserRole

```text
admin
employee
```

## UserStatus

```text
active
disabled
```

## ContentType

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

## ReviewStatus

```text
draft
pending
approved
rejected
```

## PublishStatus

```text
unpublished
publishing
published
failed
```

## ReviewAction

```text
submit
approve
reject
```

## PublishRecordStatus

```text
publishing
success
failed
```

数据库层推荐：

```text
VARCHAR + CHECK Constraint
```

不要强依赖 PostgreSQL ENUM，降低后续 Migration 修改成本。

---

# 十一、users 表

字段：

```text
id BIGINT PK

username VARCHAR(100) NOT NULL UNIQUE

password_hash VARCHAR(255) NOT NULL

name VARCHAR(100) NOT NULL

role VARCHAR(20) NOT NULL

status VARCHAR(20) NOT NULL

created_at TIMESTAMPTZ NOT NULL

updated_at TIMESTAMPTZ NOT NULL

deleted_at TIMESTAMPTZ NULL
```

约束：

```text
role IN ('admin', 'employee')

status IN ('active', 'disabled')
```

索引：

```text
username UNIQUE

role

status

deleted_at
```

用户删除：

```text
逻辑删除
deleted_at = now()
```

不要物理删除历史用户。

---

# 十二、contents 表

字段：

```text
id BIGINT PK

title VARCHAR(255) NOT NULL

description TEXT NULL

category VARCHAR(100) NULL

content_type VARCHAR(50) NOT NULL

source_file_name VARCHAR(255) NULL

source_file_path VARCHAR(1000) NULL

content_body TEXT NULL

publish_target_id BIGINT NULL

review_status VARCHAR(20) NOT NULL DEFAULT 'draft'

publish_status VARCHAR(20) NOT NULL DEFAULT 'unpublished'

reject_reason TEXT NULL

view_url VARCHAR(1000) NULL

published_at TIMESTAMPTZ NULL

created_by BIGINT NOT NULL

created_at TIMESTAMPTZ NOT NULL

updated_at TIMESTAMPTZ NOT NULL

deleted_at TIMESTAMPTZ NULL
```

外键：

```text
created_by → users.id

publish_target_id → publish_targets.id
```

不要 `ON DELETE CASCADE`。

推荐：

```text
RESTRICT / NO ACTION
```

约束：

```text
content_type IN (
  'html',
  'dynamic',
  'ppt',
  'pdf',
  'word',
  'excel',
  'image',
  'file'
)

review_status IN (
  'draft',
  'pending',
  'approved',
  'rejected'
)

publish_status IN (
  'unpublished',
  'publishing',
  'published',
  'failed'
)
```

索引：

```text
created_by
content_type
category
review_status
publish_status
published_at
publish_target_id
deleted_at
(review_status, publish_status)
```

---

# 十三、publish_targets 表

字段：

```text
id BIGINT PK

name VARCHAR(100) NOT NULL

content_types JSONB NOT NULL

publish_root VARCHAR(1000) NOT NULL

base_url VARCHAR(1000) NOT NULL

enabled BOOLEAN NOT NULL DEFAULT true

created_by BIGINT NOT NULL

created_at TIMESTAMPTZ NOT NULL

updated_at TIMESTAMPTZ NOT NULL
```

这里必须使用 PostgreSQL：

```text
JSONB
```

SQLAlchemy：

```python
from sqlalchemy.dialects.postgresql import JSONB
```

不要将 `content_types` 保存成 JSON 字符串 TEXT。

外键：

```text
created_by → users.id
```

索引：

```text
enabled
created_by
```

第一阶段不要求 GIN 索引。

应用层验证 `content_types` 只能包含：

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

---

# 十四、review_records 表

字段：

```text
id BIGINT PK

content_id BIGINT NOT NULL

action VARCHAR(30) NOT NULL

from_status VARCHAR(20) NULL

to_status VARCHAR(20) NOT NULL

comment TEXT NULL

operated_by BIGINT NOT NULL

created_at TIMESTAMPTZ NOT NULL
```

约束：

```text
action IN ('submit', 'approve', 'reject')
```

外键：

```text
content_id → contents.id

operated_by → users.id
```

历史审核记录不允许 CASCADE 删除。

索引：

```text
content_id
action
operated_by
created_at
(content_id, created_at)
```

---

# 十五、publish_records 表

字段：

```text
id BIGINT PK

content_id BIGINT NOT NULL

publish_target_id BIGINT NOT NULL

status VARCHAR(20) NOT NULL

source_path VARCHAR(1000) NULL

output_path VARCHAR(1000) NULL

publish_url VARCHAR(1000) NULL

message TEXT NULL

error_message TEXT NULL

triggered_by BIGINT NOT NULL

started_at TIMESTAMPTZ NULL

finished_at TIMESTAMPTZ NULL

created_at TIMESTAMPTZ NOT NULL
```

状态约束：

```text
status IN (
  'publishing',
  'success',
  'failed'
)
```

外键：

```text
content_id → contents.id

publish_target_id → publish_targets.id

triggered_by → users.id
```

索引：

```text
content_id
publish_target_id
status
triggered_by
created_at
(content_id, created_at)
```

每次重新发布：

```text
新增 publish_record
```

绝不能覆盖旧记录。

---

# 十六、operation_logs 表

字段：

```text
id BIGINT PK

user_id BIGINT NULL

action VARCHAR(100) NOT NULL

target_type VARCHAR(50) NULL

target_id BIGINT NULL

message TEXT NULL

ip_address VARCHAR(100) NULL

created_at TIMESTAMPTZ NOT NULL
```

外键：

```text
user_id → users.id
```

不要 CASCADE。

索引：

```text
user_id
action
(target_type, target_id)
created_at
```

---

# 十七、数据库 Relationship

合理建立：

```text
User.contents
Content.creator

User.publish_targets
PublishTarget.creator

Content.publish_target
PublishTarget.contents

Content.review_records
ReviewRecord.content

Content.publish_records
PublishRecord.content
```

历史记录关系不要配置危险的：

```python
cascade="all, delete-orphan"
```

---

# 十八、逻辑删除规则

用户：

```text
users.deleted_at
```

内容：

```text
contents.deleted_at
```

发布目标：

```text
优先 enabled=false
```

审核记录：

```text
不删除
```

发布记录：

```text
不删除
```

操作日志：

```text
不删除
```

Repository 默认过滤：

```text
deleted_at IS NULL
```

不要让每个 Router 自己处理逻辑删除过滤。

---

# 十九、数据库 Migration

必须使用：

```text
Alembic
```

不要将：

```python
Base.metadata.create_all()
```

作为正式数据库版本管理方式。

允许开发测试辅助使用，但正式初始化必须通过 Migration。

---

# 二十、Alembic

必须正确配置：

```text
alembic.ini
alembic/env.py
alembic/versions/
```

`alembic/env.py` 从应用配置读取：

```text
DATABASE_URL
```

不要把数据库账号密码写死在：

```text
alembic.ini
```

Initial Migration 必须创建：

```text
users
publish_targets
contents
review_records
publish_records
operation_logs
```

并实际创建：

```text
Primary Key
Foreign Key
Unique
CHECK Constraint
Index
Default
NOT NULL
```

必须实现：

```python
upgrade()
downgrade()
```

---

# 二十一、认证方案

使用：

```text
JWT Bearer Token
```

密码：

```text
pwdlib + Argon2
```

如果项目已有 bcrypt，可沿用 bcrypt。

绝对禁止：

```text
明文密码
SHA256(password)
MD5(password)
```

自行作为密码保存方式。

---

# 二十二、认证 API

实现：

```text
POST /api/auth/login

POST /api/auth/logout

GET /api/auth/me
```

登录 Response：

```json
{
  "success": true,
  "data": {
    "token": "...",
    "user": {
      "id": 1,
      "username": "employee",
      "name": "Employee",
      "role": "employee",
      "status": "active"
    }
  },
  "message": ""
}
```

`logout` 在纯 JWT MVP 中可以由前端删除 token。

后端接口仍保留：

```text
POST /api/auth/logout
```

返回成功即可。

本阶段不要额外引入 Redis token blacklist。

---

# 二十三、认证依赖

实现：

```python
get_current_user()
```

职责：

```text
解析 Bearer Token
↓
校验 JWT
↓
查询 PostgreSQL User
↓
确认 deleted_at IS NULL
↓
确认 status = active
↓
返回 CurrentUser
```

实现：

```python
require_admin()
```

管理员接口必须真实后端鉴权。

普通员工访问管理员接口：

```text
403 Forbidden
```

---

# 二十四、禁用用户

如果：

```text
status = disabled
```

即使 Token 未过期：

所有受保护 API 仍必须拒绝访问。

不能只在登录时检查用户状态。

---

# 二十五、统一 API 返回

统一：

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

分页：

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

---

# 二十六、HTTP 状态码

正确使用：

```text
200
201
400
401
403
404
409
422
500
```

不要所有业务错误都返回 200。

---

# 二十七、统一异常体系

建议实现：

```text
AuthenticationError

PermissionDenied

ResourceNotFound

BusinessRuleError

InvalidFileError

PublishError
```

集中 exception handler。

禁止 Router 到处：

```python
try:
    ...
except Exception:
    ...
```

---

# 二十八、Health API

实现：

```text
GET /api/health
```

返回：

```json
{
  "success": true,
  "data": {
    "status": "ok"
  },
  "message": ""
}
```

可以同时做简单 PostgreSQL：

```text
SELECT 1
```

确认数据库连接。

不要扩展成复杂监控系统。

---

# 二十九、用户管理 API

仅管理员：

```text
GET    /api/users
POST   /api/users
GET    /api/users/{id}
PUT    /api/users/{id}
PATCH  /api/users/{id}/status
DELETE /api/users/{id}
```

用户列表支持：

```text
keyword
role
status
page
page_size
```

删除采用逻辑删除。

Response 永远不能返回：

```text
password_hash
```

---

# 三十、内容 API

实现：

```text
GET    /api/contents

POST   /api/contents

GET    /api/contents/{id}

PUT    /api/contents/{id}

DELETE /api/contents/{id}

POST   /api/contents/{id}/submit

POST   /api/contents/{id}/publish

POST   /api/contents/{id}/republish

GET    /api/contents/{id}/preview
```

---

# 三十一、内容列表权限

管理员：

```text
可以查看全部未逻辑删除内容
```

普通员工：

```text
只返回 created_by = 当前用户
```

即使普通员工传：

```text
created_by=其他用户ID
```

也不能绕过后端权限。

---

# 三十二、内容筛选

支持：

```text
keyword
content_type
category
review_status
publish_status
created_by
page
page_size
```

关键词第一阶段：

```text
title
description
```

PostgreSQL 使用：

```text
ILIKE
```

不要引入全文搜索引擎。

---

# 三十三、内容创建

接口：

```text
POST /api/contents
```

文件类使用：

```text
multipart/form-data
```

字段：

```text
title
description
category
content_type
publish_target_id
file
content_body
```

默认状态必须由后端 / 数据库保证：

```text
review_status = draft
publish_status = unpublished
```

不能依赖前端传状态。

---

# 三十四、文件上传存储

原始文件：

```text
绝对不能直接写正式发布目录
```

先保存到：

```text
SOURCE_STORAGE_ROOT
```

例如：

```text
storage/source/{content_id}/{uuid}.pptx
```

数据库保存：

```text
source_file_name
source_file_path
```

`source_file_name`：

```text
用户看到的原始文件名
```

真实磁盘文件：

```text
后端生成 UUID
```

避免文件名冲突。

---

# 三十五、上传文件安全

必须防止：

```text
../
..\
路径穿越
绝对路径覆盖
危险文件名
```

要求：

1. 用户不能提交任意服务器路径。
2. 后端自己决定 source 存储位置。
3. 使用 `Path.resolve()`。
4. 验证结果位于 `SOURCE_STORAGE_ROOT` 内。
5. 限制文件大小。
6. 根据 content_type 检查扩展名。

配置：

```env
MAX_UPLOAD_SIZE_MB=100
```

---

# 三十六、内容类型与文件扩展名

至少合理验证：

```text
ppt
→ .ppt .pptx

pdf
→ .pdf

word
→ .doc .docx

excel
→ .xls .xlsx

image
→ 常用图片

html
→ .html .htm
```

`file`：

```text
允许其他普通文件
```

不要只相信前端传来的 `content_type`。

---

# 三十七、内容修改权限

管理员：

```text
可修改全部内容
```

普通员工：

```text
只能修改自己的内容
```

且：

```text
review_status = pending
```

时不能修改。

普通员工主要允许编辑：

```text
draft
rejected
```

---

# 三十八、内容删除权限

普通员工：

```text
只能删除自己的内容
```

且：

```text
publish_status = published
```

时第一阶段禁止普通员工直接删除。

管理员可逻辑删除所有内容。

---

# 三十九、提交审核

接口：

```text
POST /api/contents/{id}/submit
```

普通员工只能提交：

```text
自己创建的内容
```

合法状态：

```text
draft
rejected
```

提交后：

```text
review_status = pending
```

同时新增：

```text
review_records(action='submit')
operation_logs(action='submit_content')
```

---

# 四十、提交审核事务

提交必须使用同一个数据库事务完成：

```text
UPDATE contents
+
INSERT review_records
+
INSERT operation_logs
```

失败全部 rollback。

---

# 四十一、审核 API

仅管理员：

```text
GET  /api/reviews

GET  /api/reviews/{content_id}

POST /api/reviews/{content_id}/approve

POST /api/reviews/{content_id}/reject
```

审核列表默认：

```text
status=pending
```

支持：

```text
status
keyword
content_type
category
submitted_by
date_from
date_to
page
page_size
```

---

# 四十二、审核详情

返回：

```text
内容基本信息
创建人
原始文件信息
预览信息
发布目标
审核历史
```

管理员可以看到发布目标：

```text
publish_root
base_url
```

普通员工任何接口都不能暴露：

```text
publish_root
output_path
服务器物理目录
```

---

# 四十三、审核驳回

接口：

```text
POST /api/reviews/{content_id}/reject
```

Request：

```json
{
  "comment": "请修改标题"
}
```

要求：

```text
comment 必填
```

只有：

```text
review_status = pending
```

才能驳回。

执行：

```text
review_status = rejected
reject_reason = comment
```

新增：

```text
review_record(action='reject')
operation_log(action='reject_content')
```

---

# 四十四、审核通过

接口：

```text
POST /api/reviews/{content_id}/approve
```

合法状态：

```text
review_status = pending
```

审核前必须验证：

```text
publish_target 存在

publish_target.enabled = true

content_type 属于 publish_target.content_types
```

然后执行：

```text
review_status = approved

publish_status = publishing

新增 review_record(action='approve')

新增 publish_record(status='publishing')

新增 operation_log(action='approve_content')
```

---

# 四十五、审核通过事务边界

不要让 PostgreSQL 长事务覆盖整个文件发布过程。

推荐：

## Transaction A

```text
SELECT Content ... FOR UPDATE

验证状态

review_status = approved

publish_status = publishing

INSERT review_record

INSERT publish_record(status=publishing)

INSERT operation_log

COMMIT
```

然后执行文件发布。

发布成功：

## Transaction B

```text
contents.publish_status = published

contents.view_url = ...

contents.published_at = ...

publish_records.status = success

publish_records.publish_url = ...

publish_records.output_path = ...

publish_records.finished_at = ...

COMMIT
```

发布失败：

```text
contents.publish_status = failed

publish_records.status = failed

publish_records.error_message = ...

publish_records.finished_at = ...

COMMIT
```

审核已经通过后，发布失败：

```text
review_status 仍然 = approved
```

绝对不能回到 pending。

---

# 四十六、PostgreSQL 并发保护

审核和重新发布时建议：

```text
SELECT ... FOR UPDATE
```

SQLAlchemy：

```python
select(Content).where(...).with_for_update()
```

防止两个管理员同时操作同一内容。

如果：

```text
publish_status = publishing
```

再次 publish / republish：

```text
409 Conflict
```

---

# 四十七、管理员直接发布

接口：

```text
POST /api/contents/{id}/publish
```

仅管理员。

用于管理员创建内容后直接发布。

必须复用同一个：

```text
PublishService
```

流程：

```text
review_status = approved
publish_status = publishing
↓
PublishService
↓
published / failed
```

仍然要创建：

```text
ReviewRecord
PublishRecord
OperationLog
```

不要单独写第二套发布逻辑。

---

# 四十八、重新发布

接口：

```text
POST /api/contents/{id}/republish
```

仅管理员。

至少支持：

```text
review_status = approved
publish_status = failed
```

执行：

```text
failed
↓
publishing
↓
PublishService
↓
published / failed
```

每次都新增：

```text
publish_records
```

禁止覆盖旧失败记录。

---

# 四十九、发布目标 API

实现：

```text
GET    /api/publish-targets

POST   /api/publish-targets

GET    /api/publish-targets/{id}

PUT    /api/publish-targets/{id}

PATCH  /api/publish-targets/{id}/status

DELETE /api/publish-targets/{id}
```

---

# 五十、发布目标读取权限

管理员：

返回：

```text
id
name
content_types
publish_root
base_url
enabled
```

普通员工：

只返回：

```text
id
name
content_types
enabled
```

普通员工绝不能看到：

```text
publish_root
```

---

# 五十一、发布目标写权限

以下全部只允许 admin：

```text
POST
PUT
PATCH
DELETE
```

employee：

```text
403
```

---

# 五十二、发布目标删除

如果已有：

```text
contents.publish_target_id
```

引用当前目标：

```text
禁止删除
```

返回：

```text
409 Conflict
```

提示：

```text
该发布目标已被内容使用，请改为禁用
```

不要数据库 CASCADE 删除。

---

# 五十三、PublishService

建立：

```text
app/services/publish_service.py
```

职责：

```text
读取 Content
↓
读取 PublishTarget
↓
验证 target.enabled
↓
验证内容类型匹配
↓
生成安全 relative_path
↓
选择 Publisher
↓
Publisher 生成发布文件
↓
写入 publish_root
↓
生成 view_url
↓
更新 PostgreSQL 状态
↓
更新 PublishRecord
```

---

# 五十四、Publisher 抽象

建立：

```text
BasePublisher
```

统一接口。

示意：

```python
class PublishResult:
    relative_path: str
    output_path: str
    view_url: str
```

Publisher 只负责：

```text
处理自己的内容类型
生成可发布文件
```

数据库状态统一由：

```text
PublishService
```

管理。

---

# 五十五、PublisherFactory

映射：

```text
html
→ HtmlPublisher

dynamic
→ DynamicPagePublisher

ppt
→ PptPublisher

pdf
→ PdfPublisher

word
→ WordPublisher

excel
→ ExcelPublisher

image
→ ImagePublisher

file
→ FilePublisher
```

以后替换某种转换逻辑时：

```text
只修改对应 Publisher
```

不能影响 API / 审核 / 数据库整体结构。

---

# 五十六、第一阶段发布策略

本阶段优先保证流程完整。

## HTML

`content_body`：

```text
生成 index.html
```

上传 `.html`：

```text
复制并生成可访问入口
```

## Dynamic

单独保留：

```text
DynamicPagePublisher
```

第一阶段可以基于 `content_body` 生成页面。

不要和 HtmlPublisher 完全写死在一起。

## PDF

```text
复制 PDF
+
生成 index.html
```

通过：

```text
iframe / object
```

查看。

## Image

```text
复制图片
+
生成 index.html
```

## PPT / PPTX

如果当前项目没有可靠 PPT→HTML 转换器：

```text
复制源文件
+
生成查看 / 下载页面
```

保留：

```text
PptPublisher
```

后续再替换为：

```text
PPT → SVG / HTML
```

## Word

```text
复制文件
+
生成查看 / 下载入口
```

## Excel

```text
复制文件
+
生成查看 / 下载入口
```

## File

```text
复制文件
+
生成统一下载页面
```

不要因为高级文件转换尚未实现而阻塞 MVP。

---

# 五十七、发布路径

建议：

```text
{content_id}-{safe_slug}
```

例如：

```text
1001-bim-proposal/
```

最终目录：

```text
publish_root/
└─ 1001-bim-proposal/
   ├─ index.html
   └─ files/
```

最终 URL：

```text
base_url + relative_path
```

前端绝对不能自己拼 URL。

---

# 五十八、发布目录安全

对于：

```text
publish_root
```

和生成路径：

必须：

```python
Path.resolve()
```

并确认最终输出仍然位于目标 `publish_root` 内。

禁止目录穿越。

普通员工只能传：

```text
publish_target_id
```

不能传：

```text
publish_root
output_path
absolute_path
```

---

# 五十九、发布 URL

使用后端统一函数正确拼接：

```text
base_url
+
relative_path
```

避免：

```text
//
```

和漏 `/`。

返回并保存：

```text
contents.view_url
publish_records.publish_url
```

---

# 六十、发布失败处理

所有 Publisher 异常统一由：

```text
PublishService
```

捕获。

失败必须保证：

```text
Content.review_status = approved

Content.publish_status = failed

PublishRecord.status = failed

PublishRecord.error_message != null

PublishRecord.finished_at != null
```

数据库不能永久停留：

```text
publishing
```

---

# 六十一、内容预览

接口：

```text
GET /api/contents/{id}/preview
```

管理员：

```text
可以预览全部内容
```

普通员工：

```text
只能预览自己的后台内容
或已经发布的内容
```

Response：

```json
{
  "success": true,
  "data": {
    "preview_type": "url",
    "preview_url": "..."
  },
  "message": ""
}
```

或者：

```json
{
  "success": true,
  "data": {
    "preview_type": "text",
    "content": "<html>...</html>"
  },
  "message": ""
}
```

---

# 六十二、预览安全

不能提供：

```text
/api/preview?path=/some/server/path
```

这类任意路径读取接口。

预览必须通过：

```text
content_id
```

或后端生成的安全资源标识。

每次读取都重新检查权限。

---

# 六十三、内容检索

实现：

```text
GET /api/search
```

管理员和普通员工都可以使用。

只返回：

```text
publish_status = published

deleted_at IS NULL
```

的内容。

支持：

```text
keyword
content_type
category
date_from
date_to
page
page_size
```

keyword：

```text
title ILIKE
description ILIKE
```

---

# 六十四、搜索结果

返回：

```text
id
title
description
content_type
category
published_at
view_url
```

普通员工不得看到：

```text
source_file_path
publish_root
output_path
数据库配置
```

---

# 六十五、发布记录 API

仅管理员：

```text
GET /api/publish-records

GET /api/publish-records/{id}
```

支持：

```text
content_id
status
content_type
date_from
date_to
page
page_size
```

默认：

```text
created_at DESC
```

---

# 六十六、操作日志 API

仅管理员：

```text
GET /api/logs/operations
```

支持：

```text
user_id
action
date_from
date_to
page
page_size
```

默认：

```text
created_at DESC
```

发布日志直接复用：

```text
GET /api/publish-records
```

不要做重复接口。

---

# 六十七、必须记录的操作日志

至少：

```text
login

create_user
update_user
disable_user
enable_user
delete_user

create_content
update_content
delete_content
submit_content

approve_content
reject_content

publish_content
republish_content

create_publish_target
update_publish_target
enable_publish_target
disable_publish_target
delete_publish_target
```

---

# 六十八、Dashboard API

实现：

```text
GET /api/dashboard
```

管理员：

```json
{
  "content_total": 120,
  "pending_review": 8,
  "published": 100,
  "publish_failed": 2,
  "recent_submissions": [],
  "recent_publishes": []
}
```

普通员工：

```json
{
  "my_content_total": 15,
  "pending_review": 2,
  "published": 11,
  "rejected": 2,
  "recent_contents": [],
  "recent_publishes": []
}
```

普通员工统计只允许：

```text
created_by = current_user.id
```

---

# 六十九、分页

以下必须分页：

```text
GET /api/users
GET /api/contents
GET /api/reviews
GET /api/publish-records
GET /api/search
GET /api/logs/operations
```

统一：

```text
page=1
page_size=20
```

限制：

```text
page_size <= 100
```

SQL：

```text
LIMIT / OFFSET
```

---

# 七十、Repository

至少：

## UserRepository

```text
get_by_id
get_by_username
list
create
update
soft_delete
```

## ContentRepository

```text
get_by_id
get_for_update
list
create
update
soft_delete
search_published
```

## PublishTargetRepository

```text
get_by_id
list
create
update
is_in_use
```

## ReviewRepository

```text
list
list_by_content
create_record
```

## PublishRecordRepository

```text
list
get_by_id
create
update_status
list_by_content
```

## OperationLogRepository

```text
list
create
```

---

# 七十一、避免 N+1

列表需要：

```text
creator
publish_target
```

时使用：

```text
selectinload
```

或：

```text
joinedload
```

避免明显 N+1 查询。

---

# 七十二、默认排序

建议：

```text
用户
→ created_at DESC

内容
→ updated_at DESC

审核
→ created_at DESC

发布记录
→ created_at DESC

操作日志
→ created_at DESC

搜索
→ published_at DESC
```

---

# 七十三、数据库事务

必须事务化：

```text
用户创建 / 修改
内容创建 / 修改
提交审核
审核驳回
审核通过状态初始化
管理员直接发布初始化
重新发布初始化
发布成功状态更新
发布失败状态更新
```

不要出现：

```text
Content 已改状态
但 ReviewRecord 没创建
```

这种不一致。

---

# 七十四、CORS

读取：

```env
CORS_ORIGINS=http://localhost:5173
```

开发允许 Vue 访问。

生产不要直接：

```text
*
```

如果使用 Bearer Token，不需要为了 CORS 关闭安全策略。

---

# 七十五、Swagger / OpenAPI

FastAPI 保持：

```text
/docs
/redoc
```

API tags：

```text
Health
Auth
Users
Contents
Reviews
Publish Targets
Publish Records
Search
Logs
Dashboard
```

每个接口尽量定义：

```text
response_model
summary
description
```

前端开发者应能直接通过 `/docs` 对接。

---

# 七十六、API 最小清单

最终至少：

```text
Health
GET    /api/health

Auth
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

Users
GET    /api/users
POST   /api/users
GET    /api/users/{id}
PUT    /api/users/{id}
PATCH  /api/users/{id}/status
DELETE /api/users/{id}

Contents
GET    /api/contents
POST   /api/contents
GET    /api/contents/{id}
PUT    /api/contents/{id}
DELETE /api/contents/{id}
POST   /api/contents/{id}/submit
POST   /api/contents/{id}/publish
POST   /api/contents/{id}/republish
GET    /api/contents/{id}/preview

Reviews
GET    /api/reviews
GET    /api/reviews/{content_id}
POST   /api/reviews/{content_id}/approve
POST   /api/reviews/{content_id}/reject

Publish Targets
GET    /api/publish-targets
POST   /api/publish-targets
GET    /api/publish-targets/{id}
PUT    /api/publish-targets/{id}
PATCH  /api/publish-targets/{id}/status
DELETE /api/publish-targets/{id}

Publish Records
GET    /api/publish-records
GET    /api/publish-records/{id}

Search
GET    /api/search

Logs
GET    /api/logs/operations

Dashboard
GET    /api/dashboard
```

---

# 七十七、Seed

创建：

```text
scripts/seed.py
```

开发用户：

```text
admin
password: admin123
role: admin
```

```text
employee
password: employee123
role: employee
```

密码必须 Hash。

Seed 必须幂等。

重复执行不能重复插入相同 username。

---

# 七十八、Seed 开发发布目标

可增加：

```text
HTML 发布区
PPT 发布区
PDF 发布区
文档发布区
图片发布区
公共文件区
```

例如：

```json
{
  "name": "PPT 发布区",
  "content_types": ["ppt"],
  "publish_root": "./published/presentation/",
  "base_url": "http://localhost:8081/presentation/",
  "enabled": true
}
```

这些只用于开发。

不要假设生产目录和开发目录相同。

---

# 七十九、测试要求

使用：

```text
pytest
```

测试数据库必须使用：

```text
TEST_DATABASE_URL
```

对应独立 PostgreSQL Test DB。

绝不能跑测试时连接正式数据库。

---

# 八十、认证测试

覆盖：

```text
正确密码登录

错误密码 → 401

disabled 用户不能登录

disabled 用户持旧 Token 访问 API → 403

employee 调 admin API → 403
```

---

# 八十一、数据库约束测试

覆盖：

```text
username 唯一

role=superadmin 被拒绝

content_type=video 被拒绝

Content 默认：
review_status=draft
publish_status=unpublished

不存在 publish_target_id 被拒绝
```

---

# 八十二、员工内容权限测试

覆盖：

```text
employee 创建内容成功

employee 修改自己 draft 成功

employee 修改自己 rejected 成功

employee 修改 pending 失败

employee 修改别人内容 → 403

employee 删除自己 published 内容失败
```

---

# 八十三、提交审核测试

验证：

```text
draft
↓
pending
```

同时：

```text
ReviewRecord submit
OperationLog submit_content
```

都创建成功。

---

# 八十四、驳回测试

验证：

```text
pending
↓
rejected
```

同时：

```text
reject_reason
ReviewRecord reject
OperationLog reject_content
```

正确。

---

# 八十五、发布成功测试

验证：

```text
pending
↓
approved + publishing
↓
Publisher
↓
published
```

最终：

```text
view_url != null

published_at != null

PublishRecord.status = success

ReviewRecord.action = approve
```

---

# 八十六、发布失败测试

模拟 Publisher 抛异常。

最终必须：

```text
review_status = approved

publish_status = failed

PublishRecord.status = failed

error_message != null
```

---

# 八十七、重新发布测试

第一次：

```text
PublishRecord #1 = failed
```

第二次：

```text
PublishRecord #2 = success
```

两条必须同时存在。

---

# 八十八、发布目录权限测试

employee：

```text
GET /api/publish-targets
```

Response 不能包含：

```text
publish_root
```

employee：

```text
POST /api/publish-targets
```

必须：

```text
403
```

---

# 八十九、搜索测试

数据库存在：

```text
draft
pending
rejected
published
failed
```

内容。

```text
GET /api/search
```

只能返回：

```text
published
```

---

# 九十、并发状态测试

同一 Content：

```text
publish_status = publishing
```

再次：

```text
publish
republish
```

必须：

```text
409
```

如果方便，增加两个并发审核尝试，验证 `FOR UPDATE` / 状态检查至少保证只有一次成功。

---

# 九十一、Alembic 测试

实际执行：

```bash
alembic upgrade head
```

必须成功。

然后确认：

```text
6 张表
FK
CHECK
INDEX
JSONB
TIMESTAMPTZ
```

正确。

至少测试一次：

```bash
alembic downgrade -1
```

再：

```bash
alembic upgrade head
```

确保 migration 可逆。

---

# 九十二、requirements

建议使用一个：

```text
requirements.txt
```

或者当前项目如果已有：

```text
pyproject.toml
```

则沿用。

不要同时维护两套冲突依赖。

至少需要：

```text
fastapi
uvicorn
sqlalchemy
psycopg
alembic
pydantic
pydantic-settings
python-multipart
PyJWT 或 python-jose
pwdlib[argon2] 或项目已有密码库
pytest
httpx
```

---

# 九十三、README

必须写：

```text
README.md
```

至少包括：

1. 项目介绍
2. 技术栈
3. Python 版本
4. PostgreSQL 要求
5. 创建数据库
6. 创建测试数据库
7. 虚拟环境
8. 安装依赖
9. `.env`
10. `DATABASE_URL`
11. `TEST_DATABASE_URL`
12. Alembic Migration
13. Seed
14. 启动 FastAPI
15. Swagger 地址
16. pytest
17. 用户角色
18. 内容状态
19. 发布状态
20. 文件存储
21. 发布目录配置
22. 如何新增 Publisher

PostgreSQL 示例：

```sql
CREATE DATABASE content_publish;
CREATE DATABASE content_publish_test;
```

Migration：

```bash
alembic upgrade head
```

Seed：

```bash
python scripts/seed.py
```

启动：

```bash
uvicorn app.main:app --reload
```

---

# 九十四、开发顺序

Codex 按以下顺序执行。

## Phase 1：检查现有项目

检查：

```text
当前 FastAPI 结构
已有 requirements
已有 SQLAlchemy
已有 Alembic
已有 .env
已有数据库代码
```

如果已有：

```text
基于现有项目修改
```

---

## Phase 2：统一 PostgreSQL

删除或修改所有：

```text
SQLite fallback
sqlite:///...
MySQL 配置
多数据库兼容说明
```

统一：

```text
PostgreSQL + psycopg
```

---

## Phase 3：基础工程

完成：

```text
config
database session
CORS
统一 response
统一 exception
health
```

确认：

```text
FastAPI 能启动
PostgreSQL 能连接
```

---

## Phase 4：ORM + Alembic

完成：

```text
6 张 Model
Relationship
CHECK
Index
JSONB
TIMESTAMPTZ
FK
Alembic
```

实际运行：

```bash
alembic upgrade head
```

---

## Phase 5：认证 / 用户

完成：

```text
JWT
密码 Hash
auth
me
admin dependency
用户 CRUD
禁用
逻辑删除
```

---

## Phase 6：内容管理

完成：

```text
内容 CRUD
上传
文件安全
权限
预览
逻辑删除
分页
筛选
```

---

## Phase 7：审核

完成：

```text
submit
reviews
approve
reject
ReviewRecord
FOR UPDATE
状态事务
```

---

## Phase 8：发布目标

完成：

```text
PublishTarget CRUD
JSONB content_types
管理员 / 员工响应字段差异
类型匹配
删除限制
```

---

## Phase 9：自动发布

完成：

```text
PublishService
PublisherFactory
8 个 Publisher
目录安全
view_url
PublishRecord
成功
失败
重新发布
```

---

## Phase 10：Search / Logs / Dashboard

完成：

```text
search
publish records
operation logs
dashboard
```

---

## Phase 11：Seed

实际执行：

```bash
python scripts/seed.py
```

确认：

```text
admin
employee
publish targets
```

正确。

---

## Phase 12：测试

运行：

```bash
pytest
```

修复所有失败。

---

## Phase 13：最终检查

实际确认：

```text
FastAPI 启动正常

PostgreSQL 正常

alembic upgrade head 正常

/docs 正常

pytest 正常

完整员工 → 审核 → 发布流程正常

普通员工无法看到物理发布目录
```

---

# 九十五、完整验收业务场景

必须实际验证：

```text
admin 登录
↓
创建 employee
↓
employee 登录
↓
上传 PPT
↓
Content = draft / unpublished
↓
employee submit
↓
pending
↓
ReviewRecord submit
↓
admin 查看 reviews
↓
admin reject
↓
rejected
↓
employee 修改
↓
重新 submit
↓
pending
↓
admin approve
↓
approved + publishing
↓
PublishRecord publishing
↓
PptPublisher
↓
读取 PostgreSQL PublishTarget
↓
生成安全发布目录
↓
生成 view_url
↓
published
↓
PublishRecord success
↓
employee GET /api/search
↓
找到已发布内容
↓
通过 view_url 打开
↓
admin 查看 OperationLog
↓
admin 查看 PublishRecord
```

---

# 九十六、最终架构

最终结构：

```text
Vue 3 + TypeScript
        ↓
      REST API
        ↓
      FastAPI
        ↓
┌──────────────────────┐
│ AuthService          │
│ UserService          │
│ ContentService       │
│ ReviewService        │
│ PublishTargetService │
│ PublishService       │
│ SearchService        │
│ DashboardService     │
│ LogService           │
└──────────────────────┘
        ↓
   Repositories
        ↓
 SQLAlchemy 2.x
        ↓
   PostgreSQL
```

发布部分：

```text
PublishService
        ↓
PublisherFactory
        ↓
┌─────────────────────┐
│ HtmlPublisher       │
│ DynamicPublisher    │
│ PptPublisher        │
│ PdfPublisher        │
│ WordPublisher       │
│ ExcelPublisher      │
│ ImagePublisher      │
│ FilePublisher       │
└─────────────────────┘
        ↓
PublishTarget
        ↓
publish_root
+
base_url
```

---

# 九十七、最终最重要的约束

Codex 开发过程中必须始终遵守：

```text
1. PostgreSQL 是唯一数据库。

2. 不再实现 SQLite fallback。

3. PostgreSQL 使用 psycopg 3。

4. 数据库变化全部由 Alembic 管理。

5. publish_targets.content_types 使用 JSONB。

6. 时间使用 TIMESTAMPTZ。

7. 审核状态与发布状态严格分离。

8. ReviewRecord 保存完整审核历史。

9. PublishRecord 保存每一次发布历史。

10. 用户和内容采用逻辑删除。

11. 发布目标被使用时不能级联删除。

12. 普通员工永远不能看到 publish_root。

13. 前端永远不能直接指定服务器物理路径。

14. 前端永远不能自行计算 view_url。

15. PublishService 是正式发布的唯一入口。

16. Publisher 只负责内容类型处理。

17. Router 不直接操作文件系统和数据库细节。

18. 发布文件处理失败不能破坏审核状态。

19. 发布失败后管理员可以直接重新发布，不重新审核。

20. 不为 MVP 擅自引入 Redis / Celery / MQ / 微服务。
```

---

# 九十八、Codex 执行要求

不要只输出代码建议或架构说明。

必须实际：

```text
检查项目
创建 / 修改文件
安装 / 调整依赖
连接 PostgreSQL
创建 Migration
运行 Migration
实现 API
实现 Service
实现 Repository
实现 Publisher
运行 Seed
运行 pytest
启动 FastAPI
检查 Swagger
修复错误
更新 README
```

如果执行过程中发现当前项目已有实现与本提示词冲突：

```text
优先在现有项目中做最小必要修改
```

不要无故推翻整个项目。

最终项目必须能够真正运行，而不是只有示例代码。
