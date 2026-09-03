# Codex 开发任务：公司内部内容自动发布平台前端

你是一名高级 Vue 3 + TypeScript 前端工程师。

请根据当前项目中的以下需求文档，实现“公司内部内容自动发布平台”的前端：

- `01_功能说明.md`
- `02_前端页面.md`

这两个文件是本次开发的业务需求基准。

如果本提示词与需求文档发生冲突，以本提示词中明确规定的技术实现原则为优先；业务范围不得擅自扩大。

---

# 一、项目目标

实现一个公司内部使用的内容自动发布平台前端。

系统只存在两个角色：

```text
admin     管理员
employee  普通员工
```

核心业务流程：

```text
登录
 ↓
创建 / 上传内容
 ↓
普通员工提交发布申请
 ↓
管理员审核
 ├─ 驳回
 │   ↓
 │ 员工修改
 │   ↓
 │ 重新提交
 │
 └─ 审核通过
      ↓
    后端自动发布
      ↓
    返回发布 URL
      ↓
员工检索
      ↓
查看已发布内容
```

前端重点是：

1. 登录
2. 用户管理
3. 内容管理
4. 普通员工提交审核
5. 管理员审核
6. 发布状态展示
7. 发布目录配置
8. 内容检索
9. 日志查看

---

# 二、技术栈

必须使用：

```text
Vue 3
TypeScript
Vite
Vue Router
Pinia
Axios
Element Plus
```

编码方式：

```text
Vue 3 Composition API
<script setup lang="ts">
```

禁止使用：

```text
Vue 2
Options API
JavaScript-only
jQuery
```

---

# 三、开发原则

## 3.1 前后端完全解耦

前端只能通过 REST API 与后端通信。

前端不得：

- 直接读取服务器物理目录
- 直接写服务器目录
- 自己执行发布
- 自己转换 PPT / PDF / Word
- 自己计算真实服务器文件路径
- 在普通员工界面暴露服务器物理路径

所有发布操作都由后端执行。

前端只负责：

```text
用户操作
↓
调用 API
↓
展示 API 返回结果
```

---

# 四、项目结构

请整理为清晰的模块化结构。

建议：

```text
src/
├─ api/
│  ├─ request.ts
│  ├─ auth.ts
│  ├─ users.ts
│  ├─ contents.ts
│  ├─ reviews.ts
│  ├─ publishTargets.ts
│  ├─ search.ts
│  ├─ logs.ts
│  └─ dashboard.ts
│
├─ assets/
│
├─ components/
│  ├─ AppLayout/
│  ├─ ContentForm/
│  ├─ ContentStatus/
│  ├─ ContentPreview/
│  ├─ FileUploader/
│  ├─ SearchFilter/
│  ├─ EmptyState/
│  └─ PageHeader/
│
├─ layouts/
│  └─ MainLayout.vue
│
├─ pages/
│  ├─ Login/
│  ├─ Dashboard/
│  ├─ Contents/
│  ├─ Reviews/
│  ├─ Users/
│  ├─ PublishTargets/
│  ├─ Search/
│  ├─ Logs/
│  ├─ Forbidden/
│  └─ NotFound/
│
├─ router/
│  └─ index.ts
│
├─ stores/
│  ├─ auth.ts
│  └─ app.ts
│
├─ types/
│  ├─ user.ts
│  ├─ content.ts
│  ├─ review.ts
│  ├─ publish.ts
│  └─ api.ts
│
├─ constants/
│  └─ index.ts
│
├─ utils/
│
├─ App.vue
└─ main.ts
```

可以根据实际代码适当调整，但必须保证：

- API 独立
- 类型定义独立
- 页面独立
- 公共组件独立
- 权限判断集中管理

不要在单个 Vue 文件里堆积整个系统。

---

# 五、API 基础设计

统一使用 Axios。

创建：

```text
src/api/request.ts
```

API Base URL 从环境变量读取：

```text
VITE_API_BASE_URL
```

例如：

```env
VITE_API_BASE_URL=http://localhost:8080/api
```

不得把后端地址写死在页面组件中。

Axios 统一处理：

- Authorization
- HTTP 错误
- 401
- 403
- 网络异常
- 统一错误提示

如果使用 Token：

```text
Authorization: Bearer {token}
```

401：

```text
清除登录状态
↓
跳转 /login
```

403：

```text
跳转 /403
```

---

# 六、登录与身份状态

实现 Pinia：

```text
stores/auth.ts
```

至少保存：

```ts
interface CurrentUser {
  id: number
  username: string
  name: string
  role: 'admin' | 'employee'
  status: 'active' | 'disabled'
}
```

需要：

```text
login()
logout()
getCurrentUser()
isAdmin
isEmployee
```

刷新浏览器后，要能够通过：

```text
GET /api/auth/me
```

重新恢复当前用户。

---

# 七、路由权限

必须实现 Vue Router 路由守卫。

公共页面：

```text
/login
```

登录用户页面：

```text
/
/contents
/contents/new
/contents/:id
/contents/:id/edit
/search
```

管理员专属页面：

```text
/reviews
/reviews/:contentId
/users
/settings/publish-targets
/logs
```

普通员工直接访问管理员页面：

```text
→ /403
```

未登录访问业务页面：

```text
→ /login
```

不要只通过“隐藏菜单”实现权限。

路由本身必须有权限检查。

---

# 八、整体 Layout

登录页之外统一使用后台 Layout。

结构：

```text
┌────────────────────────────────────────────┐
│ Header                                     │
├──────────────┬─────────────────────────────┤
│              │                             │
│ Sidebar      │         Main Content        │
│              │                             │
│              │                             │
└──────────────┴─────────────────────────────┘
```

Header：

- 系统名称
- 当前用户名
- 当前角色
- 退出登录

Sidebar 根据角色动态显示。

---

# 九、管理员菜单

管理员显示：

```text
首页
内容管理
审核管理
内容检索
用户管理
发布配置
日志
```

底部：

```text
退出登录
```

---

# 十、普通员工菜单

普通员工显示：

```text
首页
我的内容
内容检索
```

底部：

```text
退出登录
```

不要向普通员工显示：

```text
审核管理
用户管理
发布配置
日志
```

---

# 十一、P01 登录页面

路由：

```text
/login
```

页面要求：

- 系统名称
- 用户名
- 密码
- 登录按钮
- 登录 Loading
- 登录失败提示

调用：

```text
POST /api/auth/login
```

成功后：

```text
GET /api/auth/me
```

然后进入：

```text
/
```

如果已经登录，再访问 `/login`，自动跳到首页。

---

# 十二、P02 首页 Dashboard

路由：

```text
/
```

根据角色展示不同数据。

## 管理员

显示 4 个统计指标：

```text
内容总数
待审核
已发布
发布失败
```

下面显示：

### 最近提交

字段：

```text
标题
提交人
类型
提交时间
状态
```

### 最近发布

字段：

```text
标题
类型
发布时间
发布状态
```

快捷按钮：

```text
新建内容
查看待审核
内容检索
```

---

## 普通员工

显示：

```text
我的内容
待审核
已发布
已驳回
```

下面：

### 最近编辑

### 最近发布

快捷按钮：

```text
新建内容
我的内容
内容检索
```

---

# 十三、P03 内容列表

路由：

```text
/contents
```

这是主要业务页面。

顶部：

```text
页面标题
新建内容
```

筛选区域：

```text
关键词
内容类型
分类
审核状态
发布状态
查询
重置
```

管理员：

```text
查看所有人的内容
```

普通员工：

```text
只查看自己的内容
```

表格字段：

```text
标题
类型
分类
创建人
审核状态
发布状态
更新时间
操作
```

普通员工可以不显示“创建人”，因为全部是本人内容。

---

# 十四、审核状态显示

统一封装：

```text
ContentStatus
```

审核状态：

```text
draft
→ 草稿

pending
→ 待审核

approved
→ 审核通过

rejected
→ 已驳回
```

Element Plus Tag 显示即可。

不要在每个页面重复写状态映射逻辑。

---

# 十五、发布状态显示

发布状态：

```text
unpublished
→ 未发布

publishing
→ 发布中

published
→ 已发布

failed
→ 发布失败
```

发布中需要明显 Loading / 状态提示。

---

# 十六、内容列表操作

## 管理员

根据状态显示：

```text
查看
编辑
删除
审核
重新发布
打开页面
```

例如：

`review_status = pending`

显示：

```text
查看
审核
```

`publish_status = failed`

显示：

```text
查看
重新发布
```

`publish_status = published`

显示：

```text
查看
打开页面
```

---

## 普通员工

根据状态显示：

### draft

```text
查看
编辑
删除
提交发布
```

### pending

```text
查看
```

不能编辑。

### rejected

```text
查看
编辑
重新提交
```

### published

```text
查看
打开页面
```

---

# 十七、P04 新建 / 编辑内容

路由：

```text
/contents/new
/contents/:id/edit
```

使用统一 ContentForm。

字段：

```text
标题 *
简介
分类 *
内容类型 *
文件 / 内容数据 *
发布目标
```

内容类型：

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

UI 显示中文：

```text
HTML 静态页面
动态页面
PPT / PPTX
PDF
Word
Excel
图片
普通文件
```

---

# 十八、文件上传

封装：

```text
FileUploader
```

要求：

- 支持点击上传
- 支持拖拽
- 显示文件名
- 显示文件大小
- 删除重新选择
- 上传 Loading
- 上传失败提示

根据内容类型限制合理文件扩展名。

例如：

```text
ppt → .ppt .pptx
pdf → .pdf
word → .doc .docx
excel → .xls .xlsx
image → 常见图片格式
html → .html .htm
```

普通文件可以接受其他类型。

不要在前端实现文件转换。

---

# 十九、发布目标选择

内容表单可以选择发布目标。

调用：

```text
GET /api/publish-targets
```

普通员工只能看到：

```text
发布目标名称
适用内容类型
```

例如：

```text
PPT 发布区
PDF 发布区
内部页面
公共文件
```

绝不能显示：

```text
/data/company/presentation/
```

这类服务器物理路径。

根据当前 `content_type` 自动过滤可用发布目标。

例如：

```text
content_type = ppt
```

只显示支持 PPT 的发布目标。

---

# 二十、内容表单按钮

普通员工：

```text
保存草稿
提交发布
取消
```

保存草稿：

```text
POST /api/contents
```

或：

```text
PUT /api/contents/:id
```

提交发布：

如果是新内容：

```text
先保存
↓
获得 content id
↓
POST /api/contents/:id/submit
```

如果已经存在：

```text
保存修改
↓
POST /api/contents/:id/submit
```

成功后：

```text
review_status = pending
```

---

管理员额外支持：

```text
保存并发布
```

对应：

```text
POST /api/contents/:id/publish
```

但仍然不能在前端自行发布文件。

---

# 二十一、P05 内容详情 / 预览

路由：

```text
/contents/:id
```

显示区域分为：

## 基本信息

```text
标题
简介
类型
分类
创建人
创建时间
更新时间
```

## 审核信息

```text
审核状态
驳回原因
```

如果是 rejected，驳回原因要明显展示。

## 发布信息

```text
发布状态
发布目标
发布时间
发布 URL
```

注意：

普通员工只看：

```text
发布目标名称
```

不要显示服务器物理目录。

## 内容预览

调用：

```text
GET /api/contents/:id/preview
```

根据后端返回展示。

第一阶段允许：

```text
iframe
文本
图片
文件信息
```

无法预览时：

```text
当前文件暂不支持在线预览
```

---

# 二十二、打开已发布内容

如果后端返回：

```ts
view_url
```

显示：

```text
打开内容
```

点击：

```ts
window.open(view_url, '_blank')
```

第一阶段优先采用新窗口打开。

不要自己拼接 URL。

---

# 二十三、P06 审核列表

仅管理员。

路由：

```text
/reviews
```

默认查询：

```text
review_status = pending
```

筛选：

```text
关键词
内容类型
分类
提交人
提交日期
```

表格：

```text
标题
类型
分类
提交人
提交时间
目标发布位置
操作
```

“目标发布位置”显示：

```text
发布目标名称
```

例如：

```text
PPT 发布区
```

不要在列表直接显示服务器路径。

操作：

```text
查看
审核
```

---

# 二十四、P07 审核详情

仅管理员。

路由：

```text
/reviews/:contentId
```

页面必须让管理员在一个页面完成审核。

显示：

```text
内容基本信息
内容类型
分类
创建人
提交时间
原始文件
内容预览
发布目标
历史审核记录
```

因为管理员需要确认发布目录，所以管理员可以看到：

```text
发布目标名称
服务器发布根目录
URL 根地址
```

操作：

```text
审核通过并发布
驳回
```

---

# 二十五、审核通过

点击：

```text
审核通过并发布
```

弹确认框：

```text
确认审核通过并发布该内容吗？
```

确认后：

```text
POST /api/reviews/:contentId/approve
```

前端显示 Loading。

不要连续重复提交。

API 成功：

```text
重新获取详情
更新状态
显示发布结果
```

可能出现：

```text
review_status = approved
publish_status = published
```

也可能：

```text
review_status = approved
publish_status = failed
```

第二种情况表示：

```text
审核成功
但自动发布失败
```

必须明确区分。

---

# 二十六、审核驳回

点击：

```text
驳回
```

打开 Dialog。

字段：

```text
驳回原因 *
```

调用：

```text
POST /api/reviews/:contentId/reject
```

成功后：

```text
review_status = rejected
```

员工可以重新编辑后提交。

---

# 二十七、P08 发布配置

仅管理员。

路由：

```text
/settings/publish-targets
```

这是管理员配置自动发布目录的页面。

列表字段：

```text
名称
适用内容类型
服务器发布目录
URL 根地址
状态
操作
```

操作：

```text
新增
编辑
启用
禁用
删除
```

新增 / 编辑可以使用 Dialog 或 Drawer。

字段：

```text
名称 *
适用内容类型 *
服务器发布根目录 *
URL 根地址 *
是否启用
```

例如：

```text
名称：
PPT 发布区

适用类型：
ppt

服务器发布目录：
/data/company/presentation/

URL 根地址：
https://internal.example.com/presentation/
```

必须保证：

```text
发布目录配置只存在于管理员页面
```

普通员工永远不能看到实际物理路径。

---

# 二十八、发布目标启用 / 禁用

使用 Switch。

禁用之前弹出确认。

已经被内容引用的发布目标，如果后端拒绝删除，要正确显示后端返回的信息。

前端不得通过强制删除绕过业务规则。

---

# 二十九、P09 用户管理

仅管理员。

路由：

```text
/users
```

字段：

```text
用户名
姓名
角色
状态
创建时间
操作
```

角色：

```text
admin
employee
```

显示：

```text
管理员
普通员工
```

状态：

```text
active
disabled
```

操作：

```text
新增
编辑
启用
禁用
删除
```

新增 / 编辑建议使用 Dialog。

表单：

```text
用户名
姓名
密码
角色
状态
```

编辑时密码可以为空，表示不修改。

---

# 三十、P10 日志页面

仅管理员。

路由：

```text
/logs
```

页面使用：

```text
ElTabs
```

两个 Tab：

```text
操作日志
发布日志
```

---

## 操作日志

筛选：

```text
用户
操作类型
日期范围
```

表格：

```text
时间
用户
操作
对象
说明
```

---

## 发布日志

筛选：

```text
关键词
内容类型
发布状态
日期范围
```

表格：

```text
时间
内容
发布目标
发布结果
访问 URL
失败原因
```

URL 可点击。

发布失败原因如果太长：

```text
table 显示省略
hover / dialog 查看完整内容
```

---

# 三十一、P11 内容检索

路由：

```text
/search
```

管理员和普通员工均可访问。

这是员工查找正式发布内容的入口。

顶部大搜索框：

```text
请输入内容标题或关键词
```

筛选：

```text
内容类型
分类
发布时间
```

按钮：

```text
搜索
重置
```

调用：

```text
GET /api/search
```

只显示：

```text
published
```

的内容。

---

# 三十二、搜索结果

推荐卡片或简洁列表。

每项显示：

```text
标题
简介
内容类型
分类
发布时间
```

操作：

```text
查看详情
打开内容
```

“打开内容”必须使用 API 返回的：

```text
view_url
```

不能自行拼接发布地址。

---

# 三十三、状态常量

集中定义：

```text
constants/index.ts
```

不要散落在页面。

例如：

```ts
export const REVIEW_STATUS = {
  draft: '草稿',
  pending: '待审核',
  approved: '审核通过',
  rejected: '已驳回'
}

export const PUBLISH_STATUS = {
  unpublished: '未发布',
  publishing: '发布中',
  published: '已发布',
  failed: '发布失败'
}

export const CONTENT_TYPES = {
  html: 'HTML 静态页面',
  dynamic: '动态页面',
  ppt: 'PPT / PPTX',
  pdf: 'PDF',
  word: 'Word',
  excel: 'Excel',
  image: '图片',
  file: '普通文件'
}
```

---

# 三十四、TypeScript 类型

禁止大量使用：

```ts
any
```

需要定义清晰类型。

例如：

```ts
export type UserRole = 'admin' | 'employee'

export type ReviewStatus =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'rejected'

export type PublishStatus =
  | 'unpublished'
  | 'publishing'
  | 'published'
  | 'failed'

export type ContentType =
  | 'html'
  | 'dynamic'
  | 'ppt'
  | 'pdf'
  | 'word'
  | 'excel'
  | 'image'
  | 'file'
```

---

# 三十五、API 文件

至少实现以下前端 API 封装。

## auth.ts

```text
login
logout
getCurrentUser
```

## users.ts

```text
getUsers
getUser
createUser
updateUser
updateUserStatus
deleteUser
```

## contents.ts

```text
getContents
getContent
createContent
updateContent
deleteContent
submitContent
publishContent
republishContent
getContentPreview
```

## reviews.ts

```text
getReviews
getReviewDetail
approveReview
rejectReview
```

## publishTargets.ts

```text
getPublishTargets
createPublishTarget
updatePublishTarget
updatePublishTargetStatus
deletePublishTarget
```

## search.ts

```text
searchContents
```

## logs.ts

```text
getOperationLogs
getPublishLogs
```

## dashboard.ts

```text
getDashboard
```

页面组件不得到处直接写：

```ts
axios.get(...)
```

必须经过 API 模块。

---

# 三十六、Mock 模式

考虑到前后端解耦，开发前端时后端可能尚未完成。

因此增加开发环境 Mock 能力。

建议：

```text
VITE_USE_MOCK=true
```

当：

```text
VITE_USE_MOCK=true
```

前端使用 Mock 数据。

当：

```text
VITE_USE_MOCK=false
```

调用真实后端 API。

Mock 数据必须覆盖：

```text
管理员账号
普通员工账号
草稿内容
待审核内容
已驳回内容
已发布内容
发布失败内容
用户列表
审核列表
发布目标
操作日志
发布日志
搜索结果
Dashboard
```

这样整个前端在没有后端的情况下也可以完整演示业务流程。

但 Mock 层和真实 API 层必须可替换，不要把 Mock 数据直接写死在页面中。

---

# 三十七、建议 Mock 用户

管理员：

```text
username: admin
password: admin123
role: admin
```

普通员工：

```text
username: employee
password: employee123
role: employee
```

仅用于本地开发 Mock。

不要把这些账号作为生产默认账号。

---

# 三十八、分页

以下列表必须支持分页：

```text
内容列表
审核列表
用户列表
操作日志
发布日志
搜索结果
```

统一参数建议：

```text
page
page_size
```

统一返回：

```ts
interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
```

---

# 三十九、Loading / Empty / Error

所有异步页面必须处理：

```text
Loading
空数据
请求失败
```

禁止：

```text
请求期间页面无反馈
请求失败后什么都不显示
```

使用 Element Plus：

```text
ElLoading
ElEmpty
ElMessage
ElMessageBox
```

即可。

---

# 四十、确认操作

以下危险操作必须二次确认：

```text
删除内容
删除用户
禁用用户
删除发布目标
禁用发布目标
审核通过并发布
重新发布
```

---

# 四十一、视觉设计

这是公司内部管理系统，不做花哨设计。

整体要求：

```text
简洁
专业
清晰
高信息密度
容易使用
```

推荐：

```text
浅色背景
白色内容卡片
深灰文字
适量边框
状态使用 Element Plus Tag
```

不要：

```text
大面积渐变
玻璃拟态
大量动画
过度圆角
大型营销 Banner
复杂视觉特效
```

系统重点是：

```text
操作效率
信息识别
状态清晰
```

---

# 四十二、响应式

优先：

```text
桌面端
1920×1080
1440×900
1366×768
```

这是公司内部后台系统。

要求支持窗口缩放，但第一阶段不需要专门制作复杂移动端布局。

---

# 四十三、关键业务规则

必须严格实现以下规则。

### 规则 1

普通员工只能编辑自己的内容。

### 规则 2

普通员工不能编辑：

```text
review_status = pending
```

的内容。

### 规则 3

普通员工不能直接执行正式发布。

普通员工：

```text
提交发布
→ 等待管理员审核
```

### 规则 4

管理员：

```text
审核通过
→ 后端执行自动发布
```

### 规则 5

管理员自己创建的内容允许：

```text
保存并发布
```

### 规则 6

审核通过但发布失败：

```text
review_status = approved
publish_status = failed
```

此时管理员执行：

```text
重新发布
```

不重新审核。

### 规则 7

发布 URL 完全由后端返回。

前端不得拼接。

### 规则 8

普通员工不得看到服务器物理发布路径。

### 规则 9

管理员可以配置发布目标和服务器目录。

### 规则 10

内容类型和发布目标必须匹配。

---

# 四十四、本阶段明确不开发

不要擅自加入：

```text
多级审批
复杂 RBAC 权限系统
部门管理
内容版本
发布回滚
定时发布
定时下架
消息通知
收藏
评论
点赞
标签系统
全文搜索引擎
工作流设计器
WebSocket
复杂 BI Dashboard
```

保持 MVP。

---

# 四十五、开发顺序

严格建议按照以下顺序实施。

## Phase 1：基础项目

完成：

```text
Vue 3 + TypeScript + Vite
Element Plus
Vue Router
Pinia
Axios
ESLint
基础 Layout
```

确保：

```text
npm install
npm run dev
npm run build
```

正常。

---

## Phase 2：认证与权限

完成：

```text
登录
用户状态
路由守卫
角色菜单
403
404
退出
```

---

## Phase 3：Mock API

完成：

```text
管理员
普通员工
内容
审核
发布目标
日志
搜索
Dashboard
```

保证无后端也能运行。

---

## Phase 4：内容管理

完成：

```text
内容列表
创建
编辑
详情
上传
删除
状态
提交审核
```

---

## Phase 5：管理员审核

完成：

```text
审核列表
审核详情
审核通过
审核驳回
发布结果
重新发布
```

---

## Phase 6：系统管理

完成：

```text
用户管理
发布配置
日志
```

---

## Phase 7：员工检索

完成：

```text
搜索
筛选
结果
打开内容
```

---

## Phase 8：整理

完成：

```text
Loading
Empty
Error
权限边界
类型检查
代码清理
README
```

---

# 四十六、验收场景

开发完成后必须手动验证以下场景。

## 场景 A：员工发布

```text
employee 登录
↓
新建 PPT 内容
↓
上传 .pptx
↓
选择 PPT 发布区
↓
保存草稿
↓
提交发布
↓
状态变为待审核
↓
不能继续编辑
```

---

## 场景 B：管理员驳回

```text
admin 登录
↓
审核管理
↓
打开员工内容
↓
填写驳回原因
↓
驳回
```

然后：

```text
employee 登录
↓
看到已驳回
↓
看到驳回原因
↓
修改内容
↓
重新提交
```

---

## 场景 C：审核成功发布

```text
admin
↓
审核通过并发布
↓
显示审核通过
↓
显示已发布
↓
显示 view_url
```

---

## 场景 D：发布失败

Mock：

```text
review_status = approved
publish_status = failed
```

管理员能够看到：

```text
发布失败
失败原因
重新发布
```

点击重新发布后更新状态。

---

## 场景 E：普通员工权限

员工手动访问：

```text
/users
/reviews
/settings/publish-targets
/logs
```

必须：

```text
→ /403
```

---

## 场景 F：发布目录安全

普通员工：

```text
内容创建
内容详情
内容搜索
```

任何地方都不能看到：

```text
/data/...
/var/www/...
C:\...
```

这类服务器物理目录。

---

## 场景 G：搜索

已发布内容：

```text
可以检索
可以筛选
可以打开
```

未发布内容：

```text
不能出现在公共内容检索结果中
```

---

# 四十七、README

最终必须生成：

```text
README.md
```

说明：

1. 项目介绍
2. 技术栈
3. Node.js 推荐版本
4. 安装方式
5. 启动方式
6. Build 方式
7. 环境变量
8. Mock 模式
9. 真实 API 模式
10. 管理员 / 普通员工 Mock 登录账号
11. 项目目录
12. 页面路由
13. 权限说明

---

# 四十八、代码质量要求

必须：

- TypeScript 正确建模
- 尽量避免 `any`
- 公共逻辑抽取
- API 与 UI 解耦
- 页面组件职责清晰
- 状态映射集中
- 路由权限集中
- 无明显重复代码
- 无 console error
- Build 成功

不要为了所谓“架构完整”添加大量无意义抽象。

保持：

```text
简单
清楚
容易维护
后续容易接真实后端
```

---

# 四十九、Codex 执行要求

首先检查当前项目结构。

如果当前目录已经存在 Vue 3 项目：

```text
在现有项目基础上修改
```

不要无故重新初始化整个项目。

如果当前目录为空：

```text
创建 Vue 3 + TypeScript + Vite 项目
```

然后按照以上 Phase 顺序完成开发。

在开发过程中：

1. 不要只生成伪代码。
2. 实际创建和修改项目文件。
3. 实际实现页面和交互。
4. 实际运行 TypeScript / Build 检查。
5. 发现错误立即修复。
6. 不要因为后端不存在而停止开发，使用 Mock API 完成前端。
7. 不要实现本需求之外的大型功能。
8. 不要擅自修改核心业务流程。
9. 页面完成后检查管理员与普通员工的权限差异。
10. 最终确保项目可以直接启动并演示完整流程。

---

# 五十、最终交付标准

最终前端必须能够独立演示完整业务闭环：

```text
管理员创建用户
↓
普通员工登录
↓
普通员工创建 / 上传内容
↓
保存草稿
↓
提交发布
↓
管理员看到待审核
↓
管理员预览
↓
管理员驳回
↓
员工修改重新提交
↓
管理员审核通过
↓
模拟后端自动发布
↓
返回 view_url
↓
员工通过内容检索找到内容
↓
打开已发布页面
↓
管理员查看操作日志和发布日志
```

并保证未来接入真实后端时：

```text
只需要调整 API 接口适配层和环境变量
```

不需要重写页面和业务结构。