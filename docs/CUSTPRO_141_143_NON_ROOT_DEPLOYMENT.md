# custpro.net 双机非 root 部署与上传断线排查

本文对应当前服务器结构：

- `custpro.net` 的统一外部入口是 FortiGate；
- 前端位于内网地址末尾为 `.141` 的服务器；
- FastAPI 后端和 PostgreSQL 位于内网地址末尾为 `.143` 的服务器；
- 不使用 Docker；发布账号没有 root 权限；
- 本地通过 MobaXterm 的 SFTP 面板上传代码。

文中的 `<FRONTEND_IP>`、`<BACKEND_IP>`、`<DEPLOY_USER>` 必须替换成实际值。不要只填写 `141` 或 `143`。

## 1. 当前报错的结论

登录成功说明下面这条基本链路已经连通：

```text
浏览器 -> FortiGate -> .141 -> .143 -> FastAPI -> PostgreSQL
```

`POST /api/contents` 是 `multipart/form-data` 文件上传。浏览器收到 `ERR_CONNECTION_RESET` 或 `ERR_CONNECTION_ABORTED`，而没有收到 413、422、500 等 HTTP 响应，表示 TCP 连接在返回应用 JSON 之前被某一层主动中断。重点检查：

1. FortiGate 对上传请求的大小、时长、WAF/防病毒检查限制；
2. `.141` 反向代理的请求体大小和读写超时；
3. `.143` 网关的请求体大小和读写超时；
4. `.143` 的 `/tmp`、上传目录、磁盘空间和用户配额；
5. FastAPI 进程是否在上传期间崩溃或被 OOM Killer 终止。

前端代码对创建/更新内容已经设置 10 分钟超时，后端应用上限默认为 1024 MB。因此不应继续把 Axios 的普通 15 秒超时当成这次故障原因。

浏览器日志里的 `index-BeT3ycts.js` 还是旧构建文件。当前本地 `dist/index.html` 引用的是新的哈希文件，说明服务器的前端目录没有完整替换，或 FortiGate/浏览器仍缓存旧的 `index.html`。部署时必须整体切换 `dist`，并禁止缓存 `index.html`。

## 2. 推荐生产链路

推荐让 FortiGate 终止 HTTPS：

```text
Internet / office client
  -> https://custpro.net:443
  -> FortiGate TLS termination
  -> http://<FRONTEND_IP>:18080       (.141)
       ├─ /                 静态 Vue dist
       ├─ /api/*            -> http://<BACKEND_IP>:18080
       └─ /local-published/* -> http://<BACKEND_IP>:18080
                                  ├─ /api/* -> http://127.0.0.1:18000 FastAPI
                                  └─ /local-published/* -> 发布目录

.143 FastAPI -> 127.0.0.1:15432 PostgreSQL
```

普通用户不能自行开放主机防火墙、配置 FortiGate、绑定 80/443 或安装系统级 Nginx。以下事项必须由基础设施管理员完成：

- FortiGate `custpro.net:443` 转发至 `<FRONTEND_IP>:18080`；
- 只允许 FortiGate 到 `.141:18080`；
- 只允许 `.141` 到 `.143:18080`；
- `.143:15432` 和 `.143:18000` 不向局域网开放；
- `.143` 能向互联网 443 端口访问 GitHub、Microsoft、Dropbox、Meta 等发布 API。

如果 FortiGate 不是 TLS 终止，而只是 TCP 透传，应由管理员在 `.141` 的系统 Nginx/负载均衡器配置证书和 443。不要在两层同时终止 TLS。

## 3. FortiGate 必须确认的设置

请把以下清单交给 FortiGate 管理员。不同 FortiOS/公司策略的菜单名称可能不同，以现有集群规范为准：

- 虚拟服务：`custpro.net:443 -> <FRONTEND_IP>:18080`；
- 上传请求体允许值：至少 `1100 MB`，或不小于应用 `MAX_UPLOAD_SIZE_MB` 加 multipart 开销；
- 请求/上传/空闲会话超时：至少 `900 秒`；
- 允许 `POST`、`PUT` 和 `multipart/form-data`；
- 若 WAF、IPS、DLP、反病毒会缓存或扫描大文件，为 `/api/contents` 和 `/api/contents/*` 提高检查上限；无法流式检查时，对这两个已认证接口建立受控例外，不能直接关闭整个站点的安全检查；
- 保留 `Host: custpro.net`，传递客户端 IP，并向后端表明外部协议是 HTTPS；
- 健康检查使用 `GET /healthz`，不要使用会写数据库的业务接口；
- 修改后检查 FortiGate traffic/WAF/security 日志，确认没有 `oversize`、`timeout`、`reset`、`blocked multipart` 等记录。

仅修改 Nginx/Caddy，不能覆盖 FortiGate 更小的限制。

## 4. 在本地准备发布包

在 Windows PowerShell 进入项目根目录：

```powershell
npm ci
npm run lint
npm run build
Set-Location backend
python -m pytest -q
Set-Location ..
```

确认 `dist/index.html` 中引用的 JS 文件确实存在：

```powershell
Get-Content .\dist\index.html
Get-ChildItem .\dist\assets\index-*.js
```

生成两个上传包。不要把 `.env`、发布令牌、数据库密码、`.git`、`node_modules`、本地存储或测试数据库放进压缩包：

```powershell
Compress-Archive -Path .\dist\* -DestinationPath .\custpro-frontend-dist.zip -Force
```

后端建议直接在 MobaXterm SFTP 面板上传项目目录，但排除以下内容：

```text
.git/
node_modules/
dist/
local-data/
backend/.env
backend/.pytest_cache/
backend/**/__pycache__/
*.zip
```

也可以用 Git 的已跟踪文件生成无敏感配置的源代码包：

```powershell
git archive --format=zip --output=custpro-source.zip HEAD
```

如果工作区里有尚未提交的必要改动，`git archive HEAD` 不会包含它们，应先确认发布版本或用 MobaXterm 按排除清单上传工作目录。

## 5. 用 MobaXterm 上传

分别建立到 `.141` 和 `.143` 的 SSH 会话。连接后，左侧 SFTP 面板会定位到当前账号的 home 目录。

在两台机器上先创建上传目录：

```bash
mkdir -p "$HOME/upload/custpro"
```

然后：

- 将 `custpro-frontend-dist.zip` 上传到 `.141` 的 `~/upload/custpro/`；
- 将源代码目录或 `custpro-source.zip` 上传到 `.143` 的 `~/upload/custpro/`；
- 上传完成后在远端运行 `sha256sum 文件名`，与本地 `Get-FileHash -Algorithm SHA256 文件名` 比较；
- 不要覆盖 `.143` 现有的 `backend/.env` 和凭证文件。

## 6. 部署 `.143` 后端和本机 PostgreSQL

仓库内的非 root 部署脚本会在 home 目录下安装 Micromamba、Python、Node、PostgreSQL、Caddy 和 Supervisor，无需 sudo。以下命令在 `.143` 执行。

解压一个新的发布目录：

```bash
backend_release="$HOME/releases/custpro-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backend_release"
cd "$backend_release"
unzip "$HOME/upload/custpro/custpro-source.zip"
chmod +x scripts/deploy-el9-nonroot.sh
```

如果是通过 SFTP 上传的目录，直接进入该项目根目录。

首次安装或升级：

```bash
PUBLIC_URL=https://custpro.net \
WEB_PORT=18080 \
API_PORT=18000 \
DB_PORT=15432 \
MANAGED_POSTGRES=1 \
MAX_UPLOAD_SIZE_MB=1024 \
UVICORN_WORKERS=2 \
RUN_TESTS=1 \
./scripts/deploy-el9-nonroot.sh install
```

安装后配置位于：

```text
$HOME/.local/share/content-publish/app/backend/.env
$HOME/.local/share/content-publish/config/Caddyfile
$HOME/.local/share/content-publish/config/supervisord.conf
$HOME/.local/share/content-publish/logs/
```

在 `.env` 中补齐生产令牌，例如 `PUBLISH_CREDENTIAL_<目标键>_<凭证键>`。文件权限应为 600。修改配置后执行：

```bash
chmod 600 "$HOME/.local/share/content-publish/app/backend/.env"
"$HOME/.local/share/content-publish/bin/content-publishctl" restart
"$HOME/.local/share/content-publish/bin/content-publishctl" status
```

默认脚本会同时生成 Caddy 配置。双机模式下，把
`deploy/caddy/custpro-backend-143.Caddyfile.example` 复制为实际 Caddyfile，并替换：

```text
<FRONTEND_IP>  = .141 的完整内网 IP
<PUBLISHED_ROOT> = $HOME/.local/share/content-publish/data/published
<LOG_ROOT> = $HOME/.local/share/content-publish/logs
```

先验证再重启：

```bash
"$HOME/.local/share/content-publish/runtime/bin/caddy" validate \
  --config "$HOME/.local/share/content-publish/config/Caddyfile"
"$HOME/.local/share/content-publish/bin/content-publishctl" restart
curl -v http://127.0.0.1:18080/api/health
```

如果实际 Caddy 路径不同，用 `command -v caddy` 和现有 Supervisor 配置确认，不要盲目覆盖。

### 6.1 上传磁盘和临时目录检查

FastAPI/Starlette 在处理 multipart 时可能先把较大请求写入临时文件，然后应用再按块写到源文件目录。两处都必须有足够空间和配额：

```bash
df -h "$HOME" /tmp
df -i "$HOME" /tmp
quota -s 2>/dev/null || true
du -sh "$HOME/.local/share/content-publish/data" 2>/dev/null || true
touch "$HOME/.local/share/content-publish/data/.write-test"
rm "$HOME/.local/share/content-publish/data/.write-test"
```

最新版 `scripts/deploy-el9-nonroot.sh` 会自动建立用户可写的临时目录，并把后端进程的 `TMPDIR` 指向该目录：

```bash
mkdir -p "$HOME/.local/share/content-publish/tmp"
chmod 700 "$HOME/.local/share/content-publish/tmp"
```

该目录可用空间应至少大于最大单次上传量；多用户并发时需要预留倍数空间。旧版本部署需要重新上传最新版脚本并执行 `install`，或在 Supervisor 的后端 program 中手工增加 `environment=TMPDIR="..."` 后重启。

## 7. 部署 `.141` 前端

先创建版本目录并解压：

```bash
release="$HOME/releases/custpro-web-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$release"
unzip "$HOME/upload/custpro/custpro-frontend-dist.zip" -d "$release"
test -f "$release/index.html"
find "$release/assets" -maxdepth 1 -type f | head
ln -sfn "$release" "$HOME/custpro-web-current"
```

不要把新文件直接覆盖到旧目录。版本目录加软链接可以避免 `index.html` 已更新但对应哈希 JS 尚未上传的短暂不一致，也便于回滚。

有系统 Nginx 时，请管理员使用：

- `.141`：`deploy/nginx/custpro-frontend-141.conf.example`；
- `.143`：`deploy/nginx/custpro-backend-143.conf.example`。

替换全部尖括号占位符，再执行 `nginx -t`，通过后 reload。`.141` 的 `<FRONTEND_WEB_ROOT>` 应指向 `$HOME/custpro-web-current`；系统 Nginx 用户必须对 home 路径的每一级目录有执行权限和读取权限。若公司不允许 Nginx 读取用户 home，请让管理员提供受管的 Web 根目录。

完全无 root 且 `.141` 已有用户级 Caddy 时，使用 `deploy/caddy/custpro-frontend-141.Caddyfile.example`，替换：

```text
<BACKEND_IP> = .143 的完整内网 IP
<FRONTEND_WEB_ROOT> = $HOME/custpro-web-current
<LOG_ROOT> = 用户可写日志目录
```

然后验证并由现有 Supervisor 重启 Caddy。不要在 shell 中只用 `nohup` 长期运行生产服务；机器重启或进程退出后它不会被可靠拉起。

## 8. 按层验证，定位到底是谁断开上传

### 8.1 健康检查

在 `.143`：

```bash
curl -v http://127.0.0.1:18000/api/health
curl -v http://127.0.0.1:18080/api/health
```

在 `.141`：

```bash
curl -v http://<BACKEND_IP>:18080/api/health
curl -v -H 'Host: custpro.net' http://127.0.0.1:18080/api/health
```

在本地 Windows：

```powershell
curl.exe -vk https://custpro.net/healthz
curl.exe -vk https://custpro.net/api/health
```

四个检查都应返回 200。

### 8.2 登录并生成逐级上传测试文件

在 Windows 创建 1 MB、20 MB、100 MB 测试文件：

```powershell
fsutil file createnew upload-1m.bin 1048576
fsutil file createnew upload-20m.bin 20971520
fsutil file createnew upload-100m.bin 104857600
```

用浏览器先上传 1 MB，再上传 20 MB，最后才上传实际文件。记录“文件大小”和“从点击到断线的秒数”：固定大小失败通常是请求体限制，固定时间失败通常是超时。

若要用 curl 复现，先从浏览器开发者工具中复制该请求为 curl，再把 URL 分别替换为下面三个入口；这样会保留项目当前需要的表单字段和 Authorization 请求头：

```text
http://127.0.0.1:18000/api/contents       在 .143，直达 FastAPI
http://<BACKEND_IP>:18080/api/contents    在 .141，经过 .143 网关
https://custpro.net/api/contents          在本地，经过全部链路
```

每次只新增一层：

- 直达 FastAPI 失败：检查 `.143` 后端日志、临时目录、数据目录、磁盘/配额和 OOM；
- 直达成功、经 `.143:18080` 失败：检查 `.143` Nginx/Caddy；
- 前两项成功、经 `.141` 失败：检查 `.141` Nginx/Caddy；
- 内网链路成功、域名失败：问题在 FortiGate/WAF/外部入口策略。

不要反复只在浏览器测试，否则无法判断是哪一层断开。

### 8.3 同时观察日志

上传测试时开三个 MobaXterm 终端。

`.141`：

```bash
tail -F "$HOME"/.local/share/content-publish*/logs/*access*.log 2>/dev/null
```

`.143`：

```bash
tail -F "$HOME/.local/share/content-publish/logs/"*.log
```

另一个 `.143` 终端观察进程和内核事件：

```bash
ps -fu "$USER"
dmesg --ctime 2>/dev/null | tail -n 50
```

普通用户可能无权读取完整内核日志；如怀疑 OOM，请管理员查询 `journalctl -k`。判断方法：

- `.141` 完全没有该 POST：FortiGate 在到达前端前终止；
- `.141` 有 POST，`.143` 没有：`.141` 代理或两机网络中断；
- `.143` 网关有 POST，FastAPI 没有完成记录：检查请求体接收、临时盘、进程退出；
- 返回 413：请求体上限不足；
- 返回 499：客户端或上游先断开；
- 返回 502：上游进程未运行或连接被拒；
- 返回 504：代理等待上游超时；
- 没有状态码或日志写到一半：连接被 reset，结合 FortiGate 日志定位。

## 9. 前端旧缓存处理

部署后在 `.141` 确认服务器实际页面引用的新哈希：

```bash
grep -o 'assets/index-[^" ]*\.js' "$HOME/custpro-web-current/index.html"
curl -s -H 'Host: custpro.net' http://127.0.0.1:18080/ | grep -o 'assets/index-[^" ]*\.js'
```

再在 Windows 确认公网响应：

```powershell
curl.exe -ks https://custpro.net/ | Select-String 'assets/index-.*\.js'
```

三者应一致。如果内网一致而公网仍是 `index-BeT3ycts.js`，清理 FortiGate/CDN 的 HTML 缓存或设置绕过；浏览器使用强制刷新并在 Network 面板确认 `index.html` 响应头不是长期缓存。哈希资源可以长期缓存，`index.html` 不可以。

## 10. 上线验收

依次完成：

1. `GET /healthz` 和 `GET /api/health` 经公网返回 200；
2. 登录成功；
3. 1 MB、20 MB、100 MB 上传成功；
4. 上传接近业务最大值的测试文件，确认耗时小于 900 秒；
5. 内容创建后能预览、提交、审核和发布；
6. `/local-published/...` 可通过 `https://custpro.net` 打开；
7. GitHub/OneDrive/Dropbox/Instagram 目标按各自配置完成连接测试；
8. `.143` 的 PostgreSQL、FastAPI、网关在会话退出后仍运行，并验证服务器重启后的自动启动方案；
9. 备份 `.143` PostgreSQL、源文件目录、发布目录和 `.env`，凭证备份需加密；
10. 保留上一版 `.141` 版本目录和 `.143` 应用版本，以便软链接/服务配置回滚。

完成本节后再让用户正式上传。若仍失败，请提供同一次测试的文件大小、失败耗时、`.141` 访问日志、`.143` 网关日志、后端日志和 FortiGate 对应时间段记录；这些信息足以精确定位中断层。

## 11. Local 发布目标的正确配置

`/local-published/` 后面的 URL 子目录必须与发布根目录在 `LOCAL_PUBLISHED_ROOT` 下的子目录一致。例如 URL 使用 `content`：

```text
backend/.env:
LOCAL_PUBLISHED_ROOT=/home/user/tbpub_project/local-data/published
LOCAL_PUBLISHED_BASE_URL=/local-published

发布目标：
服务器发布根目录 = local-data/published/content
URL 根地址          = /local-published/content/
```

两者最终对应同一个目录：

```text
/home/user/tbpub_project/local-data/published/content
```

`.143` 的 Nginx/Caddy 则把 `/local-published/` 映射到：

```text
/home/user/tbpub_project/local-data/published
```

如果使用非 root 安装脚本，持久化物理目录会位于 `$HOME/.local/share/content-publish/data/published`，脚本同时建立项目内 `local-data` 软链接，因此发布目标仍可填写 `local-data/published/content`，迁移环境时不必改成绝对路径。

出现“当前 URL 应对应目录”后，管理员应先编辑该 Local 发布目标，让上面两项匹配并执行“测试连接”，然后在失败记录或内容详情中点击“重新发布”。审核结果仍然保留，不需要重新提交审核。

最新版后端还会在新增或编辑 Local 发布目标时立即校验这组映射，避免内容审核通过后才发现配置错误。不要删除这项校验；否则文件可能写入成功，但浏览器仍因 URL 映射到另一个目录而返回 404。

### 11.1 当前 `runtime-data` 配置的修正

如果发布目标界面填写的是：

```text
服务器发布根目录 = /home/user/tbpub_project/runtime-data/published/content
URL 根地址          = /local-published/content/
```

那么 `.143` 实际运行后端所读取的 `backend/.env` 必须是：

```dotenv
LOCAL_PUBLISHED_ROOT=/home/user/tbpub_project/runtime-data/published
LOCAL_PUBLISHED_BASE_URL=/local-published
```

注意 `LOCAL_PUBLISHED_ROOT` 只到公共根目录 `published`，不包含目标自己的 `content` 子目录。随后创建并检查权限：

```bash
mkdir -p /home/user/tbpub_project/runtime-data/published/content
test -w /home/user/tbpub_project/runtime-data/published/content
```

`.143` 网关也必须映射同一个物理根目录。Nginx：

```nginx
location ^~ /local-published/ {
    alias /home/user/tbpub_project/runtime-data/published/;
    index index.html;
    autoindex off;
}
```

Caddy：

```caddyfile
handle_path /local-published/* {
    root * /home/user/tbpub_project/runtime-data/published
    file_server
}
```

修改后重启后端和 `.143` 网关，再在管理页面依次执行“保存配置”“测试连接”“重新发布”。如果后端仍提示期望 `local-data/published/content`，说明修改的不是运行进程实际读取的 `.env`，或进程尚未重启。可从运行命令确认工作目录：

```bash
ps -fu "$USER" | grep -E '[u]vicorn|[g]unicorn'
```

若使用本项目非 root 安装脚本，运行配置不在上传源码目录，而在 `$HOME/.local/share/content-publish/app/backend/.env`；应修改该文件并执行：

```bash
"$HOME/.local/share/content-publish/bin/content-publishctl" restart
```
