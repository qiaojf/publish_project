# 06_现有项目增加中日英多语言支持_Codex提示词

## Codex 任务

你是一名高级 Vue 3 + TypeScript / FastAPI 全栈工程师。

请在**现有公司内部内容自动发布平台**上增加多语言支持，不能破坏任何现有功能。

当前项目已具备：

- Vue 3 + TypeScript + Vite
- Vue Router / Pinia / Axios / Element Plus
- Python + FastAPI
- PostgreSQL + SQLAlchemy + Alembic
- 登录
- 管理员 / 普通员工权限
- 用户管理
- 内容管理
- 普通员工提交审核
- 管理员审核 / 驳回 / 通过
- 自动发布
- Local / SFTP / GitHub / GitHub Pages / OneDrive / Dropbox 等发布目标
- 内容检索
- 操作日志
- 发布日志

本次只增加：

- 简体中文 `zh-CN`
- 日语 `ja-JP`
- 英语 `en-US`

当前系统默认语言仍然是中文。

---

# 1. 总原则

必须遵守：

1. 不重新设计系统。
2. 不改变现有业务流程。
3. 不修改现有 API path。
4. 不修改数据库中的业务状态值。
5. 不修改角色内部值。
6. 不修改 PublishTarget `target_type`。
7. 不自动翻译用户上传或录入的业务内容。
8. 不因为 i18n 重写前端或后端。
9. 优先做最小增量修改。
10. 改造完成后必须完整回归现有功能。

语言切换只改变：

```text
系统 UI
菜单
按钮
字段标签
状态显示
提示信息
确认弹窗
表单校验
日期 / 数字显示
```

语言切换不能改变：

```text
数据库数据
API 契约
审核逻辑
权限逻辑
发布逻辑
发布 Adapter
```

---

# 2. 默认语言

默认：

```text
zh-CN
```

规则：

```text
localStorage 有合法 app_locale
→ 使用该语言

否则
→ 使用 zh-CN
```

不要根据浏览器语言自动切换。

现有用户第一次升级后仍然看到中文。

---

# 3. 前端技术

增加：

```text
vue-i18n
```

使用 Vue 3 Composition API。

如果当前项目已有 i18n：

```text
沿用现有实现，不重复创建第二套。
```

建议目录：

```text
src/
├─ i18n/
│  ├─ index.ts
│  ├─ zh-CN.ts
│  ├─ ja-JP.ts
│  └─ en-US.ts
└─ components/
   └─ LanguageSwitcher/
      └─ LanguageSwitcher.vue
```

---

# 4. vue-i18n 初始化

要求：

```text
locale = zh-CN
fallbackLocale = zh-CN
```

缺少翻译时：

```text
回退中文
```

不要让页面显示 translation key。

---

# 5. LanguageSwitcher

在以下位置增加语言选择：

```text
登录页右上角
登录后的 Header 右上角
```

显示：

```text
简体中文
日本語
English
```

切换后：

- 当前页面立即刷新文字
- 不重新登录
- 不跳转页面
- 不丢失当前表单 / 页面状态
- 写入 `localStorage.app_locale`

---

# 6. Element Plus 多语言

必须同步 Element Plus locale：

```text
zh-CN → zhCn
ja-JP → ja
en-US → en
```

检查：

```text
Pagination
DatePicker
Upload
MessageBox
Empty
Table
```

不能只翻译业务文字。

---

# 7. 内部值绝不能翻译

## 角色

内部：

```text
admin
employee
```

中文：

```text
管理员
普通员工
```

日语：

```text
管理者
一般社員
```

英语：

```text
Administrator
Employee
```

---

## 审核状态

内部：

```text
draft
pending
approved
rejected
```

中文：

```text
草稿
待审核
审核通过
已驳回
```

日语：

```text
下書き
承認待ち
承認済み
差し戻し
```

英语：

```text
Draft
Pending Review
Approved
Rejected
```

---

## 发布状态

内部：

```text
unpublished
publishing
published
failed
```

中文：

```text
未发布
发布中
已发布
发布失败
```

日语：

```text
未公開
公開処理中
公開済み
公開失敗
```

英语：

```text
Unpublished
Publishing
Published
Failed
```

---

## PublishRecord.status

内部：

```text
publishing
success
failed
```

UI 翻译即可，不修改数据库。

---

## 内容类型

内部：

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

中文：

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

日语：

```text
HTML 静的ページ
動的ページ
PPT / PPTX
PDF
Word
Excel
画像
ファイル
```

英语：

```text
Static HTML Page
Dynamic Page
PPT / PPTX
PDF
Word
Excel
Image
File
```

---

# 8. 发布平台内部值不变

保持：

```text
local
sftp
github
github_pages
onedrive
dropbox
```

品牌名可以保持：

```text
GitHub
GitHub Pages
OneDrive
Dropbox
SFTP
```

不要翻译内部 `target_type`。

---

# 9. 不翻译用户业务数据

禁止自动翻译：

```text
内容标题
内容描述
分类名
文件名
审核备注
驳回原因原文
PPT / PDF / Word / Excel 正文
HTML 正文
动态页面正文
已发布内容正文
```

本任务不是 AI 翻译项目。

---

# 10. Translation Key 规范

禁止用中文本身当 key。

错误：

```text
"保存": "Save"
```

正确：

```text
common.save
common.cancel
nav.dashboard
content.title
review.approve
publishTarget.testConnection
```

示例：

```text
common.save
common.cancel
common.confirm
common.delete
common.edit
common.search
common.reset
common.close
common.loading

nav.dashboard
nav.contents
nav.reviews
nav.search
nav.users
nav.publishTargets
nav.logs
nav.logout

login.title
login.username
login.password
login.signIn

content.create
content.edit
content.submit
content.republish

review.pending
review.approve
review.reject

logs.operation
logs.publish
```

---

# 11. 需要国际化的页面

检查当前实际项目，至少覆盖：

```text
登录
Dashboard
内容列表
新建内容
编辑内容
内容详情
内容预览
审核列表
审核详情
用户管理
发布目标配置
发布目标连接测试
内容检索
操作日志
发布日志
403
404
```

如果当前项目还有其他页面：

```text
一并处理。
```

---

# 12. 管理员菜单

中文：

```text
首页
内容管理
审核管理
内容检索
用户管理
发布配置
日志
```

日语：

```text
ホーム
コンテンツ管理
承認管理
コンテンツ検索
ユーザー管理
公開設定
ログ
```

英语：

```text
Dashboard
Content Management
Review Management
Content Search
User Management
Publish Settings
Logs
```

---

# 13. 普通员工菜单

中文：

```text
首页
我的内容
内容检索
```

日语：

```text
ホーム
自分のコンテンツ
コンテンツ検索
```

英语：

```text
Dashboard
My Content
Content Search
```

---

# 14. 页面文案覆盖范围

必须覆盖以下硬编码文本：

```text
页面标题
卡片标题
按钮
Tab
表格列
筛选项
表单 Label
Placeholder
状态 Tag
空状态
Loading
成功提示
失败提示
确认框
表单校验
Breadcrumb
Document Title
```

不能只翻译菜单。

---

# 15. 发布配置页面

当前发布目标包含：

```text
Local
SFTP
GitHub
GitHub Pages
OneDrive
Dropbox
```

配置字段标签也必须国际化。

例如 GitHub Pages：

中文：

```text
Owner
Repository
Pages Branch
仓库目录
Pages URL 根地址
凭证引用
测试连接
```

日语：

```text
Owner
Repository
Pages ブランチ
リポジトリ内ディレクトリ
Pages URL ルート
認証情報参照
接続テスト
```

英语：

```text
Owner
Repository
Pages Branch
Repository Path
Pages Base URL
Credential Reference
Test Connection
```

SFTP：

中文：

```text
主机
端口
用户名
远程目录
URL 根地址
凭证引用
```

日语：

```text
ホスト
ポート
ユーザー名
リモートディレクトリ
URL ルート
認証情報参照
```

英语：

```text
Host
Port
Username
Remote Directory
Base URL
Credential Reference
```

---

# 16. 状态与 Option 集中处理

如果现在代码中存在：

```ts
const REVIEW_STATUS = {
  draft: '草稿'
}
```

改为：

```ts
const REVIEW_STATUS = {
  draft: 'status.review.draft'
}
```

或者使用 `labelKey`。

不要把翻译后的字符串永久保存在常量里。

推荐：

```ts
{
  value: 'admin',
  labelKey: 'role.admin'
}
```

组件中：

```ts
t(item.labelKey)
```

---

# 17. 响应式翻译

语言切换后以下内容必须立即变化：

```text
菜单
表格列名
Select Option
Status Tag
按钮
Dialog
Page Title
Breadcrumb
```

不要在模块初始化时只调用一次 `t()`。

需要时使用：

```text
computed()
```

保证 locale 变化后重新计算。

---

# 18. 日期和数字

API / PostgreSQL 时间保持：

```text
UTC
ISO 8601
TIMESTAMPTZ
```

不要改数据库。

前端显示使用：

```text
Intl.DateTimeFormat
Intl.NumberFormat
```

根据当前 locale。

例如：

```text
zh-CN
ja-JP
en-US
```

不要为三种语言手写三套日期逻辑。

---

# 19. 前端表单校验

所有校验提示改为 i18n。

例如：

中文：

```text
请输入标题
请选择内容类型
请选择发布目标
```

日语：

```text
タイトルを入力してください
コンテンツタイプを選択してください
公開先を選択してください
```

英语：

```text
Please enter a title.
Please select a content type.
Please select a publish target.
```

---

# 20. Axios Accept-Language

Axios request interceptor 增加：

```http
Accept-Language: zh-CN
```

随当前 locale 改为：

```text
zh-CN
ja-JP
en-US
```

但：

```text
后端业务逻辑不能依赖语言。
```

---

# 21. 后端国际化原则

后端不要因为多语言重写。

推荐逐步给业务异常增加稳定：

```text
error_code
```

保留已有 `message`，保证兼容。

例如：

```json
{
  "success": false,
  "data": null,
  "message": "内容不存在",
  "error_code": "CONTENT_NOT_FOUND"
}
```

前端：

```text
有 error_code 对应翻译
→ 使用当前语言翻译

没有
→ fallback 到后端 message
```

---

# 22. 推荐 error_code

至少覆盖高频错误：

```text
AUTH_INVALID_CREDENTIALS
AUTH_USER_DISABLED
AUTH_UNAUTHORIZED
AUTH_FORBIDDEN

USER_NOT_FOUND
USER_USERNAME_EXISTS

CONTENT_NOT_FOUND
CONTENT_NOT_EDITABLE
CONTENT_NOT_OWNER
CONTENT_ALREADY_PUBLISHING

REVIEW_INVALID_STATUS
REVIEW_COMMENT_REQUIRED

PUBLISH_TARGET_NOT_FOUND
PUBLISH_TARGET_DISABLED
PUBLISH_TARGET_TYPE_MISMATCH
PUBLISH_TARGET_CREDENTIAL_MISSING
PUBLISH_CONNECTION_FAILED
PUBLISH_FAILED

FILE_TOO_LARGE
FILE_TYPE_NOT_SUPPORTED
UPLOAD_FAILED
```

---

# 23. 后端日志不要国际化

内部日志可以继续使用当前语言或英文。

不要为了 i18n 改：

```text
operation_logs.action
```

数据库继续保存：

```text
login
create_user
update_user
create_content
submit_content
approve_content
reject_content
publish_content
republish_content
```

前端负责翻译这些 action。

---

# 24. 数据库原则

本任务正常情况下：

```text
不需要修改 PostgreSQL schema
不需要 Alembic Migration
```

不要为了 UI 语言增加：

```text
users.locale
```

第一阶段语言偏好只存：

```text
localStorage
```

以后需要跨设备保存时再扩展。

---

# 25. 路由与页面标题

路由 path 保持：

```text
/contents
/reviews
/users
/settings/publish-targets
/logs
```

不要创建：

```text
/zh/
/ja/
/en/
```

这种多语言 URL。

如果当前使用：

```text
route.meta.title
```

改成：

```text
route.meta.i18nKey
```

例如：

```text
nav.contents
```

浏览器 `document.title` 也随语言更新。

---

# 26. 三套语言文件 Key 必须完全一致

以：

```text
zh-CN
```

作为基准。

增加检查脚本：

```text
scripts/check-i18n-keys
```

验证：

```text
zh-CN keys
=
ja-JP keys
=
en-US keys
```

增加 npm script：

```text
npm run check:i18n
```

如果缺 key：

```text
返回失败
```

---

# 27. 日语用词统一

本系统面向企业内部使用，日语应自然、简洁。

推荐：

```text
内容管理
→ コンテンツ管理

审核管理
→ 承認管理

待审核
→ 承認待ち

审核通过
→ 承認済み

驳回
→ 差し戻し

发布
→ 公開

重新发布
→ 再公開

发布目标
→ 公開先

发布配置
→ 公開設定

发布失败
→ 公開失敗

内容检索
→ コンテンツ検索

用户管理
→ ユーザー管理

操作日志
→ 操作ログ

发布日志
→ 公開ログ
```

---

# 28. 英语术语统一

统一使用：

```text
Content
Review
Approve
Reject
Publish
Republish
Publish Target
Content Search
Operation Logs
Publish Logs
User Management
```

发布统一使用：

```text
Publish
```

不要混用：

```text
Release
Deploy
Publish
```

作为同一个 UI 概念。

---

# 29. 系统名称

如果当前没有正式品牌名，可以：

中文：

```text
公司内部内容自动发布平台
```

日语：

```text
社内コンテンツ自動公開プラットフォーム
```

英语：

```text
Internal Content Publishing Platform
```

如果当前已有正式产品名称：

```text
保留品牌名，不擅自修改。
```

---

# 30. 第三方平台错误

不要把第三方原始错误直接显示给普通员工。

例如 GitHub：

```text
Bad credentials
```

转换为：

```text
PUBLISH_AUTHENTICATION_FAILED
```

UI：

中文：

```text
发布平台认证失败
```

日语：

```text
公開先の認証に失敗しました
```

英语：

```text
Publish target authentication failed.
```

技术详情可以留在管理员日志，但不能包含 Secret。

---

# 31. 开发顺序

## Phase 1：现状扫描

先扫描当前项目：

```text
所有页面
所有组件
所有中文硬编码
所有状态映射
所有 Option
所有校验提示
所有 Message / MessageBox
所有 Route Title
所有后端中文业务错误
```

生成：

```text
docs/I18N_MIGRATION_CHECKLIST.md
```

---

## Phase 2：i18n 基础

完成：

```text
vue-i18n
zh-CN
ja-JP
en-US
默认中文
中文 fallback
localStorage
```

---

## Phase 3：语言切换

完成：

```text
Login LanguageSwitcher
Header LanguageSwitcher
即时切换
刷新恢复
```

---

## Phase 4：Element Plus

同步：

```text
zhCn
ja
en
```

---

## Phase 5：公共组件

优先修改：

```text
Layout
Sidebar
Header
PageHeader
ContentStatus
EmptyState
Common Dialog
Common Message
Breadcrumb
```

---

## Phase 6：全部业务页面

按顺序：

```text
Login
Dashboard
Contents
Content Form
Content Detail
Reviews
Review Detail
Search
Users
Publish Targets
Logs
403
404
```

---

## Phase 7：状态 / 常量 / Option

去除硬编码中文 label。

改为：

```text
translation key
```

---

## Phase 8：日期和数字

统一使用 `Intl`。

---

## Phase 9：后端 error_code

在不破坏已有 Response 的前提下增加高频错误 code。

---

## Phase 10：Accept-Language

Axios 发送当前 locale。

---

## Phase 11：自动检查

执行：

```bash
npm run check:i18n
npm run build
pytest
```

---

## Phase 12：完整回归

重新测试整个原业务流程。

---

# 32. 回归测试

必须保证多语言改造后以下全部正常：

```text
admin 登录

admin 创建用户

employee 登录

employee 创建内容

保存草稿

employee 提交审核

admin 驳回

employee 修改

employee 重新提交

admin 审核通过

自动发布

发布失败

重新发布

Local 发布

SFTP 发布

GitHub 发布

GitHub Pages 发布

OneDrive 发布

Dropbox 发布

内容检索

打开已发布内容

操作日志

发布日志
```

---

# 33. 多语言专项测试

至少测试：

## 默认语言

清空 localStorage：

```text
必须显示中文。
```

## 日语

切换：

```text
日本語
```

刷新：

```text
仍为日本語。
```

## 英语

切换：

```text
English
```

刷新：

```text
仍为 English。
```

## 非法值

例如：

```text
app_locale=xx-XX
```

必须 fallback：

```text
zh-CN
```

---

# 34. 权限回归

语言切换不能影响：

```text
admin
employee
```

权限。

employee 仍然不能访问：

```text
/users
/reviews
/logs
/settings/publish-targets
```

除当前设计允许的只读 PublishTarget 接口外。

---

# 35. 状态回归

日语界面显示：

```text
承認済み
```

数据库必须仍然：

```text
approved
```

英语显示：

```text
Published
```

数据库必须仍然：

```text
published
```

这是强制验收项。

---

# 36. 发布 Adapter 回归

语言切换不能改变：

```text
credential_ref
target_type
PublishTarget.config
GitHub repo
OneDrive folder
Dropbox path
SFTP path
```

这些全部是业务配置，不参与翻译。

---

# 37. Build 与 Test

必须实际执行：

```bash
npm run check:i18n
npm run build
pytest
```

全部通过。

不能只人工点击页面。

---

# 38. README

更新 README，增加：

```text
Supported Languages

zh-CN
ja-JP
en-US

Default Language

Language Switcher

localStorage app_locale

How to Add Translation Keys

How to Add a New Language

Element Plus Locale

Backend error_code

Accept-Language
```

---

# 39. 禁止事项

禁止：

```text
修改数据库状态值为中文 / 日文

修改 role 为本地化文本

修改 API path

修改 target_type

为每种语言复制一套页面

自动翻译用户内容

自动翻译上传文件

语言切换时重新登录

语言切换时清空页面状态

为语言支持增加复杂数据库表

为了 i18n 大规模重构已有业务

删除当前中文文案而没有 fallback

把第三方 Secret 放进语言包或日志
```

---

# 40. 最终验收标准

必须全部满足：

```text
1. 默认仍然为中文。

2. 支持简体中文 / 日本語 / English。

3. 切换立即生效。

4. 刷新后保留选择。

5. 老用户未选择语言时仍显示中文。

6. 所有主要页面均已国际化。

7. Element Plus 组件同步语言。

8. 状态显示三语言正确。

9. 数据库状态值完全不变。

10. API path 完全不变。

11. role 完全不变。

12. PublishTarget target_type 完全不变。

13. 用户录入内容不自动翻译。

14. 上传文件内容不自动翻译。

15. 前端校验提示支持三语言。

16. 确认弹窗支持三语言。

17. 日志 action 能按 UI locale 翻译。

18. 高频后端错误具有稳定 error_code。

19. 未知 error_code 能 fallback 后端 message。

20. 三套 locale key 完整一致。

21. npm run check:i18n 成功。

22. npm run build 成功。

23. pytest 成功。

24. 登录 / 用户 / 内容 / 审核 / 发布 / 检索 / 日志原功能全部正常。

25. Local / SFTP / GitHub / GitHub Pages / OneDrive / Dropbox 发布能力没有被破坏。
```

---

# 41. Codex 执行要求

不要只输出设计方案。

必须实际：

```text
检查现有项目
生成 I18N_MIGRATION_CHECKLIST
安装 / 配置 vue-i18n
实现 zh-CN / ja-JP / en-US
实现 LanguageSwitcher
实现 localStorage
实现 Element Plus locale 联动
逐页面替换硬编码中文
修改状态 / Option / Constant
修改表单校验
修改 Dialog / Message
修改 Route / Breadcrumb / Document Title
实现 Intl 日期数字格式
增加 Axios Accept-Language
必要时增加后端 error_code
增加 i18n key 检查
运行 npm run check:i18n
运行 npm run build
运行 pytest
执行完整回归测试
修复所有发现问题
更新 README
```

执行原则：

```text
优先最小修改
不重新设计
不破坏现有功能
不改变业务内部值
```

最终结果必须是在当前已经正常运行的中文系统基础上，安全增加简体中文、日语、英语三语言支持。
