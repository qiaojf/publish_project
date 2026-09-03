# 公司内部内容自动发布平台 — 后端 API 设计

## 1. API 原则

建议使用 REST API。

统一前缀：

```text
/api
```

返回格式建议：

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
  "message": "内容不存在"
}
```

认证建议第一阶段使用：

```text
JWT
```

或：

```text
Session Cookie
```

只要前后端可独立部署即可。

---

# 2. 登录 API

## POST /api/auth/login

登录。

Request：

```json
{
  "username": "user01",
  "password": "******"
}
```

Response：

```json
{
  "token": "...",
  "user": {
    "id": 1,
    "name": "User 01",
    "role": "employee"
  }
}
```

---

## POST /api/auth/logout

退出登录。

---

## GET /api/auth/me

获取当前登录用户。

Response：

```json
{
  "id": 1,
  "username": "user01",
  "name": "User 01",
  "role": "employee",
  "status": "active"
}
```

---

# 3. 用户管理 API

仅管理员。

## GET /api/users

用户列表。

Query：

```text
keyword
role
status
page
page_size
```

---

## POST /api/users

新增用户。

```json
{
  "username": "user02",
  "password": "******",
  "name": "User 02",
  "role": "employee"
}
```

---

## GET /api/users/:id

用户详情。

---

## PUT /api/users/:id

修改用户。

---

## PATCH /api/users/:id/status

启用 / 禁用用户。

```json
{
  "status": "disabled"
}
```

---

## DELETE /api/users/:id

删除用户。

建议：如果用户已经产生内容和日志，后端优先采用逻辑删除。

---

# 4. 内容 API

## GET /api/contents

获取内容列表。

管理员：

```text
默认可以查看全部
```

普通员工：

```text
默认只返回自己创建的后台内容
```

Query：

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

---

## POST /api/contents

新建内容。

对于文件内容，建议使用：

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

其中：

- 文件类型使用 `file`
- HTML / 动态内容也可以使用 `content_body`

---

## GET /api/contents/:id

内容详情。

Response 核心字段：

```json
{
  "id": 1001,
  "title": "BIM Proposal",
  "content_type": "ppt",
  "category": "proposal",
  "review_status": "pending",
  "publish_status": "unpublished",
  "publish_target_id": 2,
  "view_url": null
}
```

---

## PUT /api/contents/:id

修改内容。

权限：

管理员：

```text
可修改全部内容
```

普通员工：

```text
只能修改自己创建且当前允许编辑的内容
```

---

## DELETE /api/contents/:id

删除内容。

普通员工：

- 只能删除自己创建的内容
- 已发布内容第一阶段建议不允许普通员工直接删除

管理员：

- 可删除全部内容

---

## POST /api/contents/:id/submit

提交审核。

普通员工主要使用。

前置条件：

```text
review_status = draft
或
review_status = rejected
```

执行后：

```text
review_status = pending
```

同时创建审核记录。

---

# 5. 审核 API

仅管理员。

## GET /api/reviews

获取审核列表。

Query：

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

默认：

```text
status=pending
```

---

## GET /api/reviews/:contentId

获取审核详情。

返回：

- 内容信息
- 创建人
- 文件信息
- 预览信息
- 发布目标
- 审核历史

---

## POST /api/reviews/:contentId/approve

审核通过。

Request：

```json
{
  "comment": "审核通过"
}
```

建议后端执行顺序：

```text
1. 验证管理员权限
2. review_status → approved
3. 写 review_records
4. 创建发布任务
5. 执行自动发布
6. 更新 publish_status
7. 写 publish_records
```

如果发布失败：

```text
review_status = approved
publish_status = failed
```

不要重新变成待审核。

---

## POST /api/reviews/:contentId/reject

驳回。

Request：

```json
{
  "comment": "请修改标题和内容"
}
```

执行：

```text
review_status = rejected
```

---

# 6. 管理员直接发布 API

管理员自己创建的内容如果不希望走待审核流程，可提供：

## POST /api/contents/:id/publish

仅管理员。

后端执行：

```text
review_status → approved
↓
执行自动发布
```

这样普通员工和管理员最终仍然使用同一个发布服务。

---

# 7. 重新发布 API

## POST /api/contents/:id/republish

仅管理员。

适用：

```text
publish_status = failed
```

或者管理员需要重新生成发布文件。

处理：

```text
重新运行 Processor
↓
重新发布
↓
新增一条 publish_records
```

---

# 8. 发布目标 API

仅管理员进行修改。

## GET /api/publish-targets

查询所有发布目标。

普通员工如果需要选择目标，可允许调用此接口，但后端只返回：

```text
id
name
content_types
```

不能向普通员工返回：

```text
publish_root
```

管理员返回完整信息。

---

## POST /api/publish-targets

新增发布目标。

```json
{
  "name": "PPT 发布区",
  "content_types": ["ppt", "pptx"],
  "publish_root": "/data/company-site/presentation/",
  "base_url": "https://internal.example.com/presentation/",
  "enabled": true
}
```

---

## GET /api/publish-targets/:id

发布目标详情。

---

## PUT /api/publish-targets/:id

修改发布目标。

---

## PATCH /api/publish-targets/:id/status

启用 / 禁用。

---

## DELETE /api/publish-targets/:id

删除。

如果已有内容正在使用，建议禁止直接删除，只允许禁用。

---

# 9. 发布记录 API

## GET /api/publish-records

仅管理员。

Query：

```text
content_id
status
content_type
date_from
date_to
page
page_size
```

---

## GET /api/publish-records/:id

查看一次发布的详细结果。

---

# 10. 检索 API

## GET /api/search

管理员和普通员工均可使用。

只返回已发布且允许当前用户查看的内容。

Query：

```text
keyword
content_type
category
date_from
date_to
page
page_size
```

Response：

```json
{
  "items": [
    {
      "id": 1001,
      "title": "BIM Proposal",
      "description": "...",
      "content_type": "ppt",
      "category": "proposal",
      "published_at": "2026-09-01T10:00:00+09:00",
      "view_url": "https://internal.example.com/presentation/bim-proposal/"
    }
  ],
  "total": 1
}
```

---

# 11. 日志 API

仅管理员。

## GET /api/logs/operations

操作日志。

Query：

```text
user_id
action
date_from
date_to
page
page_size
```

---

## GET /api/logs/publishes

发布日志。

也可以直接复用：

```text
GET /api/publish-records
```

第一阶段推荐直接复用，减少接口数量。

---

# 12. Dashboard API

## GET /api/dashboard

根据当前用户角色返回不同数据。

管理员：

```json
{
  "content_total": 120,
  "pending_review": 8,
  "published": 100,
  "publish_failed": 2
}
```

普通员工：

```json
{
  "my_content_total": 15,
  "pending_review": 2,
  "published": 11,
  "rejected": 2
}
```

---

# 13. 内容预览 API

## GET /api/contents/:id/preview

用于审核和内容详情页面。

根据内容类型返回：

```json
{
  "preview_type": "url",
  "preview_url": "/api/preview/xxxx"
}
```

或：

```json
{
  "preview_type": "text",
  "content": "<html>...</html>"
}
```

具体转换逻辑由后端实现。

---

# 14. 推荐的后端内部服务结构

API Controller 不直接执行复杂发布逻辑。

建议：

```text
Controller
   ↓
Service
   ↓
Repository
```

自动发布单独建立：

```text
PublishService
    ↓
ProcessorFactory
    ├─ HtmlProcessor
    ├─ PptProcessor
    ├─ PdfProcessor
    ├─ WordProcessor
    ├─ ExcelProcessor
    ├─ ImageProcessor
    ├─ FileProcessor
    └─ DynamicPageProcessor
    ↓
PublishTargetService
    ↓
Filesystem / Web Server
```

目录解析：

```text
Content
  ↓
publish_target_id
  ↓
PublishTarget
  ↓
publish_root
base_url
  ↓
PublishService
```

前端完全不参与目录计算。

---

# 15. API 最小清单

第一阶段真正必须实现的接口约 25 个。

```text
Auth
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

Users
GET    /api/users
POST   /api/users
GET    /api/users/:id
PUT    /api/users/:id
PATCH  /api/users/:id/status
DELETE /api/users/:id

Contents
GET    /api/contents
POST   /api/contents
GET    /api/contents/:id
PUT    /api/contents/:id
DELETE /api/contents/:id
POST   /api/contents/:id/submit
POST   /api/contents/:id/publish
POST   /api/contents/:id/republish
GET    /api/contents/:id/preview

Reviews
GET    /api/reviews
GET    /api/reviews/:contentId
POST   /api/reviews/:contentId/approve
POST   /api/reviews/:contentId/reject

Publish Targets
GET    /api/publish-targets
POST   /api/publish-targets
PUT    /api/publish-targets/:id
PATCH  /api/publish-targets/:id/status
DELETE /api/publish-targets/:id

Search
GET    /api/search

Logs
GET    /api/logs/operations
GET    /api/publish-records

Dashboard
GET    /api/dashboard
```
