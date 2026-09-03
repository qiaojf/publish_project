# 05_多发布目标_GitHub_OneDrive_Dropbox_公司服务器_Codex提示词

# Codex 开发任务：多发布目标适配层实现

你是一名高级 Python / FastAPI / 系统集成工程师。

当前项目已经具备：

- Vue 3 + TypeScript 前端
- Python + FastAPI 后端
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- 内容管理
- 普通员工提交发布
- 管理员审核
- PublishService
- PublishTarget
- PublisherFactory
- 发布记录
- 操作日志

本任务只扩展“发布目标适配层”，不重新设计现有系统。

目标支持：

```text
1. 本地目录 / 公司服务器目录
2. 公司远程服务器（SFTP / SSH）
3. GitHub Repository
4. GitHub Pages
5. Microsoft OneDrive
6. Dropbox
```

以后可以扩展 NAS / SMB / S3 / Azure Blob / Google Drive，但本阶段不要主动实现。

---

# 一、保持现有主流程不变

现有主流程：

```text
员工创建内容
↓
员工提交审核
↓
管理员审核
↓
审核通过
↓
PublishService
↓
自动发布
↓
返回 publish_url / view_url
↓
记录 PublishRecord
```

不要为 GitHub / OneDrive / Dropbox / SFTP 分别重新实现一套审核流程。

---

# 二、将“内容处理”和“目标发布”分开

当前项目已有不同内容类型：

```text
HTML
PPT
PDF
Word
Excel
Image
File
Dynamic
```

这些处理器负责：

```text
原始内容
↓
转换
↓
生成可发布 Artifact
```

新增的 Target Publisher 只负责：

```text
Artifact
↓
上传 / 部署到指定平台
```

最终结构：

```text
Content
   ↓
ContentProcessorFactory
   ↓
PublishArtifact
   ↓
PublishService
   ↓
PublishTarget
   ↓
TargetPublisherFactory
   ↓
目标平台
```

禁止创建：

```text
PptToGitHubPublisher
PptToDropboxPublisher
PdfToOneDrivePublisher
```

这种“内容类型 × 发布平台”组合类。

---

# 三、PublishArtifact

建议统一定义：

```python
class PublishArtifact:
    local_path: Path
    entry_file: str | None
    content_type: str
    is_directory: bool
```

例如 PPT 转 Web 后：

```text
local-data/build/1001-demo/
├─ index.html
├─ slide-001.svg
├─ slide-002.svg
└─ assets/
```

得到：

```text
local_path = .../1001-demo
entry_file = index.html
is_directory = true
```

---

# 四、扩展 PublishTarget

当前 publish_targets 需要支持不同平台。

推荐增加：

```text
target_type VARCHAR(50) NOT NULL
config JSONB NOT NULL DEFAULT '{}'
credential_ref VARCHAR(255) NULL
```

保留现有：

```text
id
name
content_types
publish_root
base_url
enabled
created_by
created_at
updated_at
```

为了兼容现有本地发布，第一阶段不要急着删除 `publish_root` 和 `base_url`。

---

# 五、target_type

只允许：

```text
local
sftp
github
github_pages
onedrive
dropbox
```

Python Enum：

```python
class PublishTargetType(str, Enum):
    LOCAL = "local"
    SFTP = "sftp"
    GITHUB = "github"
    GITHUB_PAGES = "github_pages"
    ONEDRIVE = "onedrive"
    DROPBOX = "dropbox"
```

数据库增加 CHECK Constraint，并生成 Alembic Migration。

---

# 六、config JSONB

不同平台把非敏感配置放入：

```text
publish_targets.config
```

例如：

## GitHub

```json
{
  "owner": "company",
  "repo": "internal-content",
  "branch": "main",
  "repo_path": "published/"
}
```

## GitHub Pages

```json
{
  "owner": "company",
  "repo": "published-content",
  "branch": "gh-pages",
  "repo_path": "presentations/",
  "base_url": "https://company.github.io/published-content/"
}
```

## OneDrive

```json
{
  "tenant_id": "TENANT_ID",
  "client_id": "CLIENT_ID",
  "drive_id": "DRIVE_ID",
  "folder_path": "/Company/Published/"
}
```

## Dropbox

```json
{
  "folder_path": "/Company/Published/"
}
```

## SFTP

```json
{
  "host": "192.168.1.100",
  "port": 22,
  "username": "publisher",
  "remote_root": "/var/www/company-content/",
  "base_url": "https://internal.company/content/"
}
```

---

# 七、敏感凭证

以下不能明文存进 config：

```text
GitHub Token
Microsoft Client Secret
Dropbox Token / Refresh Token
SFTP Password
SSH Private Key
```

使用：

```text
credential_ref
```

例如：

```text
credential_ref = github_company_pages
```

MVP 推荐从环境变量读取：

```env
PUBLISH_CREDENTIAL_GITHUB_COMPANY_PAGES_TOKEN=...
PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET=...
PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN=...
PUBLISH_CREDENTIAL_SFTP_INTERNAL_PASSWORD=...
```

建立：

```text
CredentialService
```

例如：

```python
get_secret(credential_ref: str, key: str)
```

不要引入 Vault 等复杂基础设施。

---

# 八、Secret 安全规则

必须满足：

```text
GET PublishTarget 永远不返回 Secret
日志永远不记录 Secret
异常信息永远不输出 Token / Password / Client Secret
普通员工看不到 credential_ref
普通员工看不到服务器内部路径
```

管理员也只能看到非敏感 config。

Secret 不回显。

---

# 九、Target Publisher 目录

新增：

```text
app/target_publishers/
├─ base.py
├─ factory.py
├─ local.py
├─ sftp.py
├─ github.py
├─ github_pages.py
├─ onedrive.py
└─ dropbox.py
```

---

# 十、统一接口

建议：

```python
class TargetPublishResult:
    success: bool
    publish_url: str | None
    remote_path: str | None
    message: str | None
```

Base：

```python
class BaseTargetPublisher(ABC):

    @abstractmethod
    def validate_target(self, target):
        ...

    @abstractmethod
    def publish(self, artifact, target) -> TargetPublishResult:
        ...

    def test_connection(self, target) -> bool:
        ...
```

---

# 十一、TargetPublisherFactory

映射：

```text
local
→ LocalTargetPublisher

sftp
→ SftpTargetPublisher

github
→ GitHubTargetPublisher

github_pages
→ GitHubPagesTargetPublisher

onedrive
→ OneDriveTargetPublisher

dropbox
→ DropboxTargetPublisher
```

PublishService 不允许出现大量平台 `if / elif`。

---

# 十二、PublishService 改造

保持现有 PublishService，只增加目标适配逻辑：

```text
1. 读取 Content
2. 读取 PublishTarget
3. 检查 enabled
4. 检查 content_type 是否允许
5. Content Processor 生成 PublishArtifact
6. TargetPublisherFactory 获取 Adapter
7. Adapter 发布
8. 获取 publish_url
9. 更新 Content
10. 更新 PublishRecord
```

示意：

```python
artifact = processor.process(content)

publisher = target_factory.get_publisher(
    target.target_type
)

result = publisher.publish(
    artifact,
    target,
)

content.view_url = result.publish_url
```

---

# 十三、LocalTargetPublisher

目标：

```text
local
```

config / 旧字段：

```text
publish_root
base_url
```

流程：

```text
Artifact
↓
复制到 publish_root/{generated_path}
↓
生成 base_url + generated_path
```

必须用：

```python
Path.resolve()
```

防止目录穿越。

---

# 十四、SFTP / 公司服务器

公司远程服务器优先使用：

```text
SFTP
```

不实现裸 FTP。

推荐 Python 库：

```text
paramiko
```

流程：

```text
连接
↓
创建 remote_root/generated_path
↓
递归上传
↓
确认入口文件
↓
返回 base_url + generated_path
```

处理：

```text
连接失败
认证失败
权限失败
目录创建失败
上传失败
timeout
```

统一抛 PublishError。

普通员工不能指定：

```text
host
remote_root
username
```

只选择已经由管理员配置好的 PublishTarget。

---

# 十五、GitHub Repository

目标：

```text
github
```

使用：

```text
GitHub REST API
```

优先使用现有 `httpx`。

不要要求服务器提前配置：

```text
git CLI
SSH Agent
Git 用户
```

config：

```json
{
  "owner": "company",
  "repo": "internal-content",
  "branch": "main",
  "repo_path": "published/"
}
```

Token 来自 CredentialService。

---

# 十六、GitHub 上传策略

单文件可以使用 Contents API。

如果 Artifact 是完整 Web 目录，尤其 PPT 转 Web 后有大量 SVG / assets：

优先使用 Git Data API：

```text
blob
tree
commit
update ref
```

一次 commit 整个发布结果。

不要几百个文件产生几百次 commit。

重新发布：

```text
更新同一个 repo_path
产生新 commit
```

---

# 十七、GitHub 与 GitHub Pages 必须分开

`github`：

```text
代表存入 Repository
```

不保证产生可直接浏览的 Web 页面。

`github_pages`：

```text
代表静态网页发布
```

适合：

```text
HTML
PPT Web Viewer
PDF Viewer
静态页面
图片页面
```

不要混用两者。

---

# 十八、GitHubPagesTargetPublisher

config：

```json
{
  "owner": "company",
  "repo": "published-content",
  "branch": "gh-pages",
  "repo_path": "content/",
  "base_url": "https://company.github.io/published-content/"
}
```

流程：

```text
Artifact
↓
上传到 branch/repo_path/generated_path
↓
commit
↓
返回预期 Pages URL
```

注意：

```text
GitHub commit 成功
≠
Pages 页面立即可访问
```

第一阶段：

```text
commit 成功
→ PublishRecord.success
```

message 可以注明：

```text
Pages 部署可能需要短暂时间
```

本阶段不必轮询 Pages Deployment。

---

# 十九、OneDrive

使用：

```text
Microsoft Graph API
```

公司内部系统优先：

```text
Microsoft Entra ID
Client Credentials Flow
```

即：

```text
管理员配置发布目标
系统服务身份负责上传
```

普通员工不需要每次 OAuth 登录。

---

# 二十、OneDrive 上传

小文件：

```text
直接上传
```

大文件：

```text
Upload Session
```

具体阈值以当前 Microsoft Graph 官方文档为准。

不要凭记忆硬编码已过时限制。

---

# 二十一、OneDrive 不是 Web Server

OneDrive 主要作为：

```text
文件分发目标
```

如果 Artifact 是完整网站目录：

```text
自动 ZIP
↓
上传 OneDrive
```

如果只是：

```text
PDF
Word
Excel
PPT 原文件
```

可以直接上传。

返回：

```text
OneDrive Web URL
```

第一阶段不要默认创建匿名公开分享链接。

---

# 二十二、Dropbox

使用：

```text
Dropbox API
```

小文件：

```text
upload
```

大文件：

```text
upload_session
```

目录 Artifact：

```text
ZIP
↓
上传
```

Dropbox 同样不是静态网站服务器。

返回：

```text
Dropbox Web Link
```

不要默认生成公开匿名链接。

---

# 二十三、ArtifactPackagingService

新增可选服务：

```text
ArtifactPackagingService
```

负责：

```text
directory
→ zip
```

用于：

```text
OneDrive
Dropbox
```

避免普通员工自己打 ZIP。

---

# 二十四、Target Capability

建议定义：

```python
class TargetCapability:
    supports_directory: bool
    supports_file: bool
    supports_web_entry: bool
```

建议：

```text
Local:
directory=true
file=true
web=true

SFTP:
directory=true
file=true
web=true（配置 base_url 时）

GitHub:
directory=true
file=true
web=false

GitHub Pages:
directory=true
file=true
web=true

OneDrive:
directory=false
file=true
web=false

Dropbox:
directory=false
file=true
web=false
```

如果目录 Artifact 发布到 OneDrive / Dropbox：

```text
自动 ZIP
```

---

# 二十五、不同内容类型的默认推荐目标

仅作为提示，不要强制写死全部规则。

```text
HTML
→ Local / SFTP / GitHub Pages

Dynamic
→ Local / SFTP
（真正动态应用不适合 GitHub Pages）

PPT Web
→ Local / SFTP / GitHub Pages

PDF
→ Local / SFTP / GitHub Pages / OneDrive / Dropbox

Word
→ Local / SFTP / OneDrive / Dropbox

Excel
→ Local / SFTP / OneDrive / Dropbox

Image
→ 全部可支持

File
→ 全部可支持
```

---

# 二十六、动态页面

如果 `dynamic` 内容实际依赖后端运行：

```text
GitHub Pages
OneDrive
Dropbox
```

不能作为有效 Web Hosting Target。

Adapter 必须拒绝不兼容发布。

不要为了通过测试把动态应用假装成静态网页。

---

# 二十七、统一发布路径

继续沿用：

```text
{content_id}-{safe_slug}
```

例如：

```text
1001-bim-proposal
```

示例：

```text
Local:
../published/1001-bim-proposal/

SFTP:
/var/www/content/1001-bim-proposal/

GitHub Pages:
content/1001-bim-proposal/

OneDrive:
/Company/Published/1001-bim-proposal.zip

Dropbox:
/Company/Published/1001-bim-proposal.zip
```

---

# 二十八、PublishRecord

现有 PublishRecord 继续使用。

至少记录：

```text
publish_target_id
status
output_path
publish_url
message
error_message
started_at
finished_at
```

可以选择增加：

```text
target_type
remote_path
external_id
```

但不要为了扩展目标重新设计整张表。

每次重新发布必须新增一条 PublishRecord。

---

# 二十九、统一错误

建议增加：

```text
PublishTargetConfigurationError
PublishTargetConnectionError
PublishAuthenticationError
PublishPermissionError
PublishUploadError
PublishTimeoutError
```

最终由 PublishService 统一转换成：

```text
PublishError
```

并写：

```text
PublishRecord.error_message
```

---

# 三十、发布失败状态

第三方发布失败时必须保持：

```text
review_status = approved
publish_status = failed
```

并：

```text
PublishRecord.status = failed
error_message != null
```

绝不能重新回到：

```text
pending
```

---

# 三十一、重试

第一阶段不引入：

```text
Celery
Redis
Kafka
RabbitMQ
```

允许 Adapter 内有限重试：

```text
timeout
临时网络错误
429
部分 5xx
```

最多：

```text
2~3 次
```

以下不重试：

```text
401
403
配置错误
无权限
```

---

# 三十二、timeout

远程发布必须设置 timeout：

```env
PUBLISH_CONNECTION_TIMEOUT_SECONDS=30
PUBLISH_OPERATION_TIMEOUT_SECONDS=300
```

禁止无限等待。

---

# 三十三、测试连接 API

增加：

```text
POST /api/publish-targets/{id}/test
```

仅管理员。

行为：

```text
Local
→ 检查目录可写

SFTP
→ 测试连接 / 登录

GitHub
→ 检查 repo / branch 权限

GitHub Pages
→ 检查 repo / branch 权限

OneDrive
→ 检查 Graph / Drive

Dropbox
→ 检查账号 API
```

连接测试：

```text
不能真正发布内容
不能创建 PublishRecord
```

Response：

```json
{
  "success": true,
  "data": {
    "connected": true
  },
  "message": "连接成功"
}
```

---

# 三十四、前端发布配置页面

在现有管理员“发布配置”页面增加：

```text
target_type
```

根据 target_type 动态展示字段。

## Local

```text
publish_root
base_url
```

## SFTP

```text
host
port
username
remote_root
base_url
credential
```

## GitHub

```text
owner
repo
branch
repo_path
credential
```

## GitHub Pages

```text
owner
repo
branch
repo_path
base_url
credential
```

## OneDrive

```text
tenant_id
client_id
drive_id
folder_path
credential
```

## Dropbox

```text
folder_path
credential
```

增加：

```text
测试连接
```

按钮。

---

# 三十五、普通员工权限

普通员工只能获取：

```text
id
name
target_type
content_types
enabled
```

不能获得：

```text
publish_root
base_url（如果属于内部管理信息可隐藏）
config
credential_ref
remote_path
host
repo 内部配置
Token
Password
Secret
```

是否展示最终可访问 URL 由发布后的：

```text
view_url
```

决定。

---

# 三十六、第三方 API 实现要求

Codex 实现时，应查阅当前官方 API 文档。

优先：

```text
GitHub Docs
Microsoft Graph Docs
Dropbox Developers Docs
Paramiko Docs
```

不要基于旧博客硬编码接口。

---

# 三十七、自动测试禁止真实上传

pytest 必须使用：

```text
Mock / Fake
```

第三方请求。

测试时不能真的向：

```text
GitHub
OneDrive
Dropbox
公司服务器
```

上传数据。

---

# 三十八、测试文件

至少增加：

```text
test_local_target_publisher.py
test_sftp_target_publisher.py
test_github_target_publisher.py
test_github_pages_target_publisher.py
test_onedrive_target_publisher.py
test_dropbox_target_publisher.py
test_publish_target_connection.py
test_publish_service_targets.py
```

---

# 三十九、测试场景

覆盖：

```text
连接成功
连接失败
认证失败
权限失败
上传成功
上传失败
timeout
429
500
```

并验证：

```text
第三方失败
→ Content.publish_status = failed
→ PublishRecord.failed
```

---

# 四十、重新发布测试

例如：

```text
第一次 GitHub Mock 500
↓
PublishRecord #1 failed

第二次 Mock success
↓
PublishRecord #2 success
```

两条必须保留。

---

# 四十一、外部凭证缺失

没有配置 GitHub / OneDrive / Dropbox / SFTP Secret 时：

```text
整个 FastAPI 仍然必须正常启动
Local 发布仍然正常
```

只有真正调用缺失凭证的平台时返回：

```text
发布目标凭证未配置
```

---

# 四十二、开发顺序

按以下顺序执行。

## Phase 1

检查现有：

```text
PublishTarget
PublishService
PublisherFactory
内容类型 Publisher
数据库 Migration
前端发布配置页面
```

---

## Phase 2

在不破坏现有逻辑前提下，明确：

```text
Content Processor
Target Publisher
```

职责。

---

## Phase 3

扩展：

```text
target_type
config JSONB
credential_ref
```

创建 Alembic Migration。

---

## Phase 4

实现：

```text
CredentialService
```

---

## Phase 5

实现：

```text
BaseTargetPublisher
TargetPublisherFactory
```

---

## Phase 6

先迁移并验证：

```text
LocalTargetPublisher
```

保证原有本地发布功能完全不退化。

---

## Phase 7

实现：

```text
SftpTargetPublisher
```

---

## Phase 8

实现：

```text
GitHubTargetPublisher
GitHubPagesTargetPublisher
```

---

## Phase 9

实现：

```text
OneDriveTargetPublisher
```

---

## Phase 10

实现：

```text
DropboxTargetPublisher
```

---

## Phase 11

增加：

```text
ArtifactPackagingService
```

支持目录 Artifact → ZIP。

---

## Phase 12

改造：

```text
PublishService
```

统一调用 TargetPublisherFactory。

---

## Phase 13

增加：

```text
POST /api/publish-targets/{id}/test
```

---

## Phase 14

修改管理员发布配置页面：

```text
target_type
动态配置
测试连接
```

---

## Phase 15

运行：

```text
Alembic
pytest
npm run build
```

修复错误。

---

# 四十三、真实人工验证

必须真实验证：

```text
Local
```

完整发布流程。

如果当前环境已有测试凭证，可额外人工验证：

```text
GitHub
GitHub Pages
OneDrive
Dropbox
SFTP
```

但自动测试和项目完成不能依赖真实外部凭证。

---

# 四十四、README

更新 README：

```text
多发布目标架构
target_type
PublishTarget config
credential_ref
Secret 环境变量
Local 配置
SFTP 配置
GitHub 配置
GitHub Pages 配置
OneDrive 配置
Dropbox 配置
测试连接
如何新增新的 Target Publisher
```

---

# 四十五、以后增加新平台

README 中明确：

以后新增：

```text
S3
Azure Blob
Google Drive
NAS
```

只需：

```text
1. 增加 target_type
2. 实现 BaseTargetPublisher
3. 注册 TargetPublisherFactory
4. 定义 config schema
5. 增加测试
6. 管理员配置页面增加对应表单
```

不修改：

```text
员工提交
管理员审核
Content
ReviewRecord
主发布流程
```

---

# 四十六、验收标准

必须满足：

```text
1. Local 发布仍然正常。

2. PublishService 没有大量平台 if/elif。

3. TargetPublisherFactory 能按 target_type 选择 Adapter。

4. Local / SFTP / GitHub / GitHub Pages / OneDrive / Dropbox 有独立 Adapter。

5. Secret 不明文存在 config。

6. Secret 不通过 GET API 返回。

7. 普通员工看不到远程服务器内部配置。

8. GitHub 与 GitHub Pages 明确区分。

9. OneDrive / Dropbox 不被当成 Web Hosting。

10. 目录 Artifact 发布到 OneDrive / Dropbox 时能自动 ZIP。

11. 发布失败正确更新 failed。

12. 重新发布保留历史 PublishRecord。

13. 外部凭证缺失不影响系统启动。

14. 管理员可以测试连接。

15. pytest 不会真实上传第三方平台。

16. 后续增加新平台不需要修改审核和内容主流程。
```

---

# 四十七、禁止事项

禁止：

```text
为每个平台重写审核逻辑

在 PublishService 塞入大量平台代码

每个平台创建独立 Content 表

GitHub Token 明文存 PostgreSQL

OneDrive Client Secret 回传前端

Dropbox Token 写日志

SSH Password 写日志

普通员工传 remote_root

普通员工传任意服务器路径

普通员工决定 GitHub Repository

为了发布功能立即引入 Celery / Redis / MQ / 微服务
```

---

# 四十八、最终目标架构

```text
Content
   ↓
ContentProcessorFactory
   ↓
PublishArtifact
   ↓
PublishService
   ↓
PublishTarget
   ↓
TargetPublisherFactory
   ↓
┌──────────────────────┐
│ Local                │
│ SFTP                 │
│ GitHub               │
│ GitHub Pages         │
│ OneDrive             │
│ Dropbox              │
└──────────────────────┘
   ↓
TargetPublishResult
   ↓
Content.view_url
PublishRecord
```

业务层只关心：

```text
是否成功
publish_url
remote_path
message
```

不关心第三方 API 实现细节。

---

# 四十九、Codex 执行要求

不要只输出设计说明。

必须实际：

```text
检查当前代码
修改数据库 Model
创建 Alembic Migration
实现 CredentialService
实现 Target Publisher 抽象
实现 Factory
实现 Local Adapter
实现 SFTP Adapter
实现 GitHub Adapter
实现 GitHub Pages Adapter
实现 OneDrive Adapter
实现 Dropbox Adapter
实现目录 ZIP
改造 PublishService
增加连接测试 API
更新管理员发布配置页
编写 Mock 测试
运行 pytest
运行 npm run build
修复错误
更新 README
```

不要破坏已有：

```text
登录
用户
内容
审核
检索
日志
本地发布
```

最终结果是在现有系统基础上增加“可插拔多发布目标能力”，而不是重新开发发布系统。
