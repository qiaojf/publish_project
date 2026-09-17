# Instagram Reels 发布配置与测试

本项目使用 Meta 官方 **Instagram API with Instagram Login** 发布 Reels。发布目标只接受一条 MP4 或 MOV 视频；内容标题和简介会合并为帖文说明。系统先把视频临时放到公网 HTTPS 目录，创建 Instagram 媒体容器，等待状态变为 `FINISHED`，再调用 `media_publish`。发布结束后临时公网副本会被删除，源文件仍保留在私有上传目录。

> `测试连接`只验证账号 ID 与 Access Token，不会向 Instagram 发布内容。

## 1. 准备 Instagram 和 Meta 应用

1. 将 Instagram 账号切换为专业账号（Business 或 Creator）。个人账号不能使用发布 API。
2. 登录 [Meta for Developers](https://developers.facebook.com/)，创建 Business 类型应用。
3. 在应用中添加 Instagram 产品，选择 **API setup with Instagram login**。
4. 在 Instagram API 配置中添加要发布的专业账号；开发阶段，账号必须属于应用允许的测试/角色范围。
5. 为应用取得以下权限：
   - `instagram_business_basic`
   - `instagram_business_content_publish`
6. 通过 Business Login for Instagram 完成授权，取得 **Instagram User access token** 和 **Instagram professional account ID**（配置页中的 `ig_user_id`）。
7. 如果要给不属于本公司或未加入应用角色的专业账号使用，需要按 Meta 要求申请 Advanced Access 和 App Review；仅发布到自己管理且已加入应用的账号，可按 Meta 当前规则使用 Standard Access。

Token 属于敏感信息，只能放在服务器环境变量中，不能填写到发布目标的 `config`。

## 2. 配置公网视频暂存地址

Meta 会从 `video_url` 主动下载视频，因此地址必须同时满足：

- 公网可访问，不能使用 `localhost`、`127.0.0.1` 或局域网 IP；
- 使用有效证书的 HTTPS；
- 不需要登录、Cookie、VPN 或额外请求头；
- 能读取后端 `LOCAL_PUBLISHED_ROOT/_instagram/` 下的临时文件和子目录；
- 反向代理允许 MP4/MOV，并把请求体/响应超时设置得足够长。

项目现有部署脚本使用 Caddy 提供 `/local-published/*`。若站点域名为 `https://publish.example.com`，推荐：

```env
LOCAL_PUBLISHED_ROOT=../local-data/published
LOCAL_PUBLISHED_BASE_URL=/local-published
```

发布目标中的 `media_base_url` 填：

```text
https://publish.example.com/local-published/_instagram/
```

如果使用 Nginx，可在 HTTPS 虚拟主机中添加等价映射（把路径换成服务器的真实绝对路径）：

```nginx
location /local-published/ {
    alias /home/your-user/apps/content-publish/local-data/published/;
    try_files $uri =404;
    types {
        video/mp4 mp4;
        video/quicktime mov;
    }
}
```

重新加载代理后，可先放一个不敏感的测试文件，并从手机关闭 Wi-Fi 后访问 HTTPS 链接确认公网可下载。不要长期把真实内容留在 `_instagram` 目录；应用会为每次发布创建随机临时子目录并自动清理。

## 3. 配置服务器 Token

假设发布目标的“凭证引用”填写：

```text
instagram_company
```

则在 `backend/.env` 中添加：

```env
PUBLISH_CREDENTIAL_INSTAGRAM_COMPANY_ACCESS_TOKEN=粘贴Instagram_User_Access_Token
```

变量名规则为：

```text
PUBLISH_CREDENTIAL_{凭证引用转大写}_{密钥名转大写}
```

本适配器的密钥名固定为 `ACCESS_TOKEN`。修改 `.env` 后必须重启后端进程。

## 4. 升级数据库并重启

Windows 开发环境：

```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
cd ..
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local.ps1
```

Linux 非 root 部署环境：

```bash
cd /你的项目目录/backend
source .venv/bin/activate
alembic upgrade head
# 然后按现有部署方式重启后端服务
```

迁移 `20260909_0008` 会加入内容类型 `video` 和发布目标类型 `instagram`。

## 5. 在管理后台新增发布目标

以管理员登录，进入“发布配置”→“新增发布目标”，填写：

| 字段 | 示例 | 说明 |
|---|---|---|
| 名称 | 公司 Instagram | 内容表单里显示的发布名称 |
| 目标类型 | Instagram Reels | 新增的发布适配器 |
| 支持内容类型 | 视频（MP4 / MOV） | 系统固定为视频，不能混选其他类型 |
| Instagram 专业账号 ID | `17841400000000000` | Meta 返回的数字 ID，不是 `@用户名` |
| Graph API 版本 | `v23.0` | 使用你的 Meta 应用当前支持的版本；版本下线前及时升级 |
| 视频公网 URL 根地址 | `https://publish.example.com/local-published/_instagram/` | 必须映射到暂存目录 |
| 凭证引用 | `instagram_company` | 对应上面的环境变量 |
| 是否启用 | 启用 | 禁用后不可被新内容选择 |

保存后点击“测试连接”。成功表示 Token 能读取配置的专业账号；它不验证 Meta 能否从公网下载某一条尚未上传的视频，因此仍需完成下一步真实发布测试。

## 6. 发布测试视频

1. 进入“新建内容”。
2. 内容类型选择“视频（MP4 / MOV）”。
3. 发布目标选择刚创建的 Instagram 目标。
4. 填写标题、简介和分类。标题与简介会合并为 Instagram caption。
5. 只选择一个 `.mp4` 或 `.mov` 文件。
6. 管理员可点击“保存并发布”；员工提交后由管理员审核发布。
7. 发布期间系统会轮询容器处理状态。只有 Meta 返回 `FINISHED` 且 `media_publish` 成功，内容才会记为“已发布”。
8. 在内容详情或发布日志中打开返回的 Instagram permalink，确认视频、说明文字和 Feed/Reels 展示。

建议测试视频采用 H.264/HEVC 视频、AAC 48 kHz 音频、23–60 FPS、9:16，时长 3 秒至 15 分钟，文件不超过 1 GB；编码不合规时 Meta 会在容器处理阶段拒绝。

## 7. 常见错误

- **凭证未配置**：确认变量名与 `credential_ref` 完全对应，且后端已经重启。
- **认证失败/没有权限**：重新授权 Token，并检查 `instagram_business_basic`、`instagram_business_content_publish`。
- **账号与配置的 ID 不一致**：`ig_user_id` 不是用户名、Facebook Page ID 或 App ID，应填写 Instagram 专业账号数字 ID。
- **创建视频容器失败**：优先从公网检查系统生成的视频 URL 是否能直接下载，并确认 HTTPS 证书完整有效。
- **视频处理失败**：用 `ffprobe` 检查容器、编码、帧率、分辨率、时长和码率是否满足 Meta 要求。
- **处理等待超时**：根据视频大小和网络情况调大 `PUBLISH_OPERATION_TIMEOUT_SECONDS`，再使用“重新发布”。

## 8. 安全提示

- 不要把 Access Token 提交到 Git，也不要在截图、录屏或日志中展示它。
- 为 Token 只申请实际需要的权限，并按 Meta 的有效期与刷新规则轮换。
- `_instagram` 是临时公网目录；应用会清理成功或失败任务产生的副本，但仍应通过监控检查异常残留。
- 正式测试会真实发布到 Instagram。项目自动化测试使用 Mock Transport，不访问真实 Meta 账号，也不会创建帖子。
