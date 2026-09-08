# 内容自动发布平台：Enterprise Linux 9 非 root 部署指南

本文适用于无法取得 `root`、不能执行 `sudo`，但可以通过 SSH 登录并在本人 HOME 目录中运行长期进程的 Enterprise Linux 9 服务器，例如：

```text
Linux web1138.sh.fuk1 5.14.0-503.40.1.ghostlock1.el9_5.x86_64 x86_64 GNU/Linux
```

配套自动部署脚本为 `scripts/deploy-el9-nonroot.sh`。全文命令都应以普通登录用户执行，不要在命令前加 `sudo`。

## 1. 非 root 部署的能力边界

普通用户不能完成以下系统级操作：

- 不能通过 `dnf` 安装系统软件；
- 不能修改系统 Nginx、系统级 systemd 或防火墙；
- 不能直接监听 `80`、`443` 等小于 1024 的端口；
- 不能保证 SSH 退出或服务器重启后用户进程仍然存活，是否允许取决于主机策略；
- 不能让被主机防火墙拦截的高端口自动对公网开放。

本方案因此使用以下架构：

```text
浏览器
  |
  |  可选：主机控制面板或管理员提供的 HTTPS / 80 / 443 反向代理
  v
Caddy 0.0.0.0:18080（普通用户进程）
  |-- /             -> Vue dist
  |-- /api/*        -> FastAPI 127.0.0.1:18000
  `-- /published/*  -> 发布内容目录

FastAPI + Supervisor（普通用户进程）
  |
  `-- PostgreSQL 127.0.0.1:15432（普通用户进程，可改用外部数据库）
```

如果服务商禁止长期进程、禁止监听高端口，也没有应用托管或反向代理控制面板，这个账号本身无法承载本系统。此时需要让管理员开放相应能力，或把服务部署到有权限的主机；脚本不能绕过主机安全策略。

## 2. 脚本会安装什么

脚本不会修改系统目录。它先下载单文件 Micromamba，再从 conda-forge 安装一套隔离运行环境：

- Python 3.12；
- Node.js 22 和 npm；
- PostgreSQL 16 客户端与服务端；
- Caddy 2；
- rsync；
- 项目 `backend/requirements.txt` 中的后端依赖；
- Supervisor 4，用于统一管理 PostgreSQL、FastAPI 和 Caddy。

默认目录如下：

```text
$HOME/.local/share/content-publish/
├── app/                    # 部署后的项目代码和前端 dist
├── bin/content-publishctl  # start/stop/restart/status 控制命令
├── config/                 # 后端、Caddy、Supervisor 和运行参数
├── data/
│   ├── source/             # 上传源文件
│   ├── preview/            # 预览产物
│   ├── build/              # 发布构建临时产物
│   └── published/          # Local 发布目标的网页根目录
├── logs/                   # 所有服务日志
├── postgres/data/          # 用户级 PostgreSQL 数据库
├── run/                    # PID 和 Supervisor socket
├── runtime/                # Python、Node、PostgreSQL、Caddy
└── tools/micromamba        # 用户级软件包管理器
```

这些目录都属于当前用户。配置和凭证目录默认权限为 `700`，敏感文件默认权限为 `600`。

## 3. 部署前检查

### 3.1 检查系统和当前身份

```bash
cat /etc/os-release
uname -m
id
printf 'HOME=%s\n' "$HOME"
```

预期结果：

- `VERSION_ID` 主版本是 `9`；
- CPU 是 `x86_64` 或 `aarch64`；
- `id -u` 不是 `0`；
- HOME 是当前用户可写目录。

### 3.2 检查基础命令

```bash
command -v bash
command -v tar
command -v curl || command -v wget
df -h "$HOME"
```

至少需要系统已有 `bash`、`tar`，以及 `curl` 或 `wget` 中的一个。首次下载和构建建议预留 6 GB 以上空间。服务器还必须能访问 Micromamba、conda-forge、PyPI 和 npm 软件源。

如果 `tar` 不支持 bzip2 解压，或 `curl`/`wget` 都不存在，需要管理员安装其中缺失的系统基础命令，或由管理员预先把 Micromamba 上传到脚本使用的位置。

### 3.3 检查默认端口

```bash
ss -lnt 2>/dev/null | grep -E ':(18080|18000|15432)[[:space:]]' || true
```

默认使用：

- `18080`：浏览器访问端口；
- `18000`：FastAPI 内部端口；
- `15432`：PostgreSQL 内部端口。

三者必须不同，并且不能已被其他程序占用。没有 `ss` 不影响安装，脚本启动时仍会因端口冲突明确失败。

## 4. 上传项目代码

将完整项目上传到服务器，例如：

```text
$HOME/publish_project
```

目录中至少应存在：

```text
package.json
package-lock.json
backend/requirements.txt
backend/alembic.ini
scripts/deploy-el9-nonroot.sh
```

可使用 SFTP、主机文件管理器或 Git。不要把本地的 `node_modules`、`dist`、`backend/.env`、私钥和访问令牌上传到服务器。

上传后执行：

```bash
cd "$HOME/publish_project"
chmod 700 scripts/deploy-el9-nonroot.sh
```

## 5. 一键部署

### 5.1 直接通过高端口访问

假设服务器允许外部访问 `18080`：

```bash
cd "$HOME/publish_project"
PUBLIC_URL="http://web1138.sh.fuk1:18080" \
  bash scripts/deploy-el9-nonroot.sh install
```

部署成功后访问：

```text
http://web1138.sh.fuk1:18080/
```

### 5.2 通过域名和现有 HTTPS 反向代理访问

如果主机控制面板或管理员会把 `https://publish.example.com` 转发到本机 `18080`：

```bash
cd "$HOME/publish_project"
PUBLIC_URL="https://publish.example.com" \
  bash scripts/deploy-el9-nonroot.sh install
```

`PUBLIC_URL` 必须是用户最终看到的完整来源地址，不能附带路径、查询参数或账号信息。它会用于 CORS 和 Local 发布内容链接。

### 5.3 自定义安装目录和发布数据根目录

安装目录和数据目录都必须是当前用户 HOME 下的独立目录，且路径不能包含空白或引号：

```bash
cd "$HOME/publish_project"
INSTALL_ROOT="$HOME/apps/content-publish" \
PUBLISH_DATA_ROOT="$HOME/company-publish-data" \
PUBLIC_URL="http://web1138.sh.fuk1:18080" \
  bash scripts/deploy-el9-nonroot.sh install
```

此时 Local 发布目标的服务器根目录是：

```text
$HOME/company-publish-data/published
```

对应 URL 根目录是：

```text
http://web1138.sh.fuk1:18080/published
```

在后台“发布目标”中配置 Local 目标时，根目录和 URL 应与这两个值一致。若首次部署后再修改 `PUBLIC_URL` 或 `PUBLISH_DATA_ROOT`，还必须显式设置 `FORCE_CONFIG=1`；执行前先备份 `backend/.env`，并用原 JWT 密钥避免用户会话全部失效。

### 5.4 使用外部 PostgreSQL

如果主机不适合运行数据库，建议使用公司现有或托管 PostgreSQL。数据库应提前创建，账号应拥有该数据库的建表、索引、读写权限：

```bash
cd "$HOME/publish_project"
MANAGED_POSTGRES=0 \
DATABASE_URL="postgresql+psycopg://content_publish:URL编码后的密码@db.example.com:5432/content_publish" \
PUBLIC_URL="https://publish.example.com" \
  bash scripts/deploy-el9-nonroot.sh install
```

密码中的 `@`、`:`、`/`、`#`、`%` 等特殊字符必须进行 URL 编码。脚本不会安装或启动本地 PostgreSQL，但仍会安装 PostgreSQL 客户端，便于迁移、检查和备份。

如需在部署时运行后端测试，必须提供与生产库完全不同的测试库：

```bash
MANAGED_POSTGRES=0 \
DATABASE_URL="postgresql+psycopg://content_publish:密码@db.example.com:5432/content_publish" \
TEST_DATABASE_URL="postgresql+psycopg://content_publish_test:密码@db.example.com:5432/content_publish_test" \
RUN_TESTS=1 \
PUBLIC_URL="https://publish.example.com" \
  bash scripts/deploy-el9-nonroot.sh install
```

不要把生产库同时用作测试库。

## 6. 自动部署参数

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `INSTALL_ROOT` | `$HOME/.local/share/content-publish` | 程序、运行时、配置和默认数据的安装根目录 |
| `SOURCE_ROOT` | 脚本所在项目的上级目录 | 上传的项目源码目录 |
| `PUBLISH_DATA_ROOT` | `$INSTALL_ROOT/data` | 上传、预览、构建和 Local 发布数据根目录，必须位于 HOME 下 |
| `PUBLIC_URL` | `http://主机名:WEB_PORT` | 浏览器最终访问地址 |
| `WEB_PORT` | `18080` | Caddy 对外高端口，范围 `1024-65535` |
| `API_PORT` | `18000` | FastAPI 内部端口 |
| `DB_PORT` | `15432` | 本地 PostgreSQL 内部端口 |
| `MANAGED_POSTGRES` | `1` | `1` 由脚本管理本地数据库；`0` 使用外部数据库 |
| `DATABASE_URL` | 自动生成 | 外部数据库连接串；传入后自动切换到外部数据库 |
| `TEST_DATABASE_URL` | 自动生成 | `RUN_TESTS=1` 时使用的独立测试库 |
| `DB_USER` | `content_publish` | 本地 PostgreSQL 用户 |
| `DB_NAME` | `content_publish` | 本地生产数据库 |
| `TEST_DB_NAME` | `content_publish_test` | 本地测试数据库 |
| `MAX_UPLOAD_SIZE_MB` | `1024` | 后端允许的一次上传总大小，范围 `1-1024` |
| `UVICORN_WORKERS` | `2` | FastAPI 工作进程数 |
| `RUN_TESTS` | `0` | `1` 在迁移后运行后端 pytest |
| `FORCE_CONFIG` | `0` | `1` 重建后端 `.env`；正常更新不要开启 |
| `ENABLE_USER_SYSTEMD` | `0` | `1` 尝试安装并启动用户级 systemd 服务 |
| `MICROMAMBA_DOWNLOAD_URL` | 官方 latest URL | 内网镜像或离线上传场景可覆盖下载地址 |

布尔值只能写 `0` 或 `1`。脚本会拒绝 root、低端口、重复端口、HOME 之外的安装/数据目录和不合法 URL。

## 7. 脚本执行流程

运行 `install` 后，脚本依次执行：

1. 下载 Micromamba，并从 conda-forge 安装 Python、Node.js、PostgreSQL、Caddy 和 rsync；
2. 使用 rsync 将源码同步到 `$INSTALL_ROOT/app`，保留服务器现有 `backend/.env`；
3. 用隔离环境中的 pip 安装后端依赖和 Supervisor，并运行 `pip check`；
4. 首次部署时执行 `initdb`，数据库只监听 `127.0.0.1:15432`；
5. 创建生产数据库和可选测试数据库，生成强随机数据库密码、JWT 密钥及初始账号密码；
6. 执行 Alembic 数据库迁移和幂等初始化数据；
7. 使用 `npm ci` 严格按照 `package-lock.json` 安装前端依赖，再执行生产构建；
8. 生成并校验 Caddy 配置，生成 Supervisor 配置；
9. 启动服务，等待 `/api/health` 健康检查通过；
10. 输出访问地址、控制命令、日志目录和初始账号文件。

任何一步失败，脚本都会以非零状态退出。不要只看终端最后一行，应同时检查上方错误和日志目录。

## 8. 初始账号、应用配置和发布凭证

首次部署后查看随机生成的初始密码：

```bash
cat "$HOME/.local/share/content-publish/config/initial-credentials.txt"
```

默认账号为初始化脚本中的管理员与员工账号；密码文件只包含脚本为首次初始化生成的密码。首次登录后应在系统中修改密码，并把初始密码转存到公司批准的密码保险库。保留此权限为 `600` 的文件可保证以后重新运行部署脚本时不会生成一份与现有账号不对应的新“初始密码”；登录密码修改后，文件中的记录不再代表当前密码。

后端生产配置位于：

```text
$HOME/.local/share/content-publish/app/backend/.env
```

编辑前备份：

```bash
cp "$HOME/.local/share/content-publish/app/backend/.env" \
   "$HOME/.local/share/content-publish/config/backend.env.backup"
chmod 600 "$HOME/.local/share/content-publish/config/backend.env.backup"
```

GitHub、OneDrive、Dropbox、SFTP 等发布凭证也应写入这个服务器端 `.env`，格式遵循项目 `backend/.env.example`：

```dotenv
PUBLISH_CREDENTIAL_GITHUB_COMPANY_PAGES_TOKEN=替换为真实令牌
PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET=替换为真实密钥
PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN=替换为真实令牌
PUBLISH_CREDENTIAL_SFTP_INTERNAL_PASSWORD=替换为真实密码
```

编辑后保持权限并重启：

```bash
chmod 600 "$HOME/.local/share/content-publish/app/backend/.env"
"$HOME/.local/share/content-publish/bin/content-publishctl" restart
```

不要把 `.env`、数据库密码、GitHub Token 或 SSH 私钥提交到 Git。

## 9. 服务管理和日志

默认安装完成后，统一使用以下命令：

```bash
CTL="$HOME/.local/share/content-publish/bin/content-publishctl"
"$CTL" status
"$CTL" stop
"$CTL" start
"$CTL" restart
```

健康检查：

```bash
curl -fsS "http://127.0.0.1:18080/api/health"
```

日志：

```bash
LOG_ROOT="$HOME/.local/share/content-publish/logs"
tail -n 200 "$LOG_ROOT/backend.log"
tail -n 200 "$LOG_ROOT/postgresql.log"
tail -n 200 "$LOG_ROOT/caddy.log"
tail -n 200 "$LOG_ROOT/caddy-access.log"
tail -n 200 "$LOG_ROOT/supervisord.log"
```

使用外部数据库时没有本地 `postgresql.log`。

## 10. 配置重启后自动启动

### 10.1 首选：主机控制面板的应用或守护进程功能

若服务商提供“开机启动”“守护进程”“应用启动命令”，填写：

```text
/home/你的用户名/.local/share/content-publish/bin/content-publishctl start
```

这通常是无 root 托管环境最可靠的方式。

### 10.2 用户级 systemd

首次部署可尝试：

```bash
cd "$HOME/publish_project"
ENABLE_USER_SYSTEMD=1 \
PUBLIC_URL="https://publish.example.com" \
  bash scripts/deploy-el9-nonroot.sh install
```

管理命令：

```bash
systemctl --user status content-publish.service
systemctl --user restart content-publish.service
journalctl --user -u content-publish.service -n 100 --no-pager
```

用户级 systemd 需要服务器提供用户会话总线。要在用户未登录时也启动，通常还需要管理员执行一次：

```text
loginctl enable-linger 你的用户名
```

普通用户通常无权自行开启 linger。如果 `systemctl --user` 报 `Failed to connect to bus`，请改用主机控制面板或下面的 crontab 方案。

### 10.3 crontab 备用方案

执行：

```bash
crontab -e
```

加入一行，把用户名替换为真实值：

```cron
@reboot sleep 30 && /home/你的用户名/.local/share/content-publish/bin/content-publishctl start >> /home/你的用户名/.local/share/content-publish/logs/cron-start.log 2>&1
```

部分共享主机不执行用户 `@reboot`，或会在登出后清理进程。配置后必须在维护窗口实际重启服务器/实例验证，不能只以 `crontab -l` 作为成功依据。

## 11. 域名、80/443 和 HTTPS

### 11.1 直接访问高端口

如果主机防火墙和云安全组允许 `18080`，可直接访问：

```text
http://服务器地址:18080/
```

若服务器本机健康检查成功，但外部浏览器超时，问题通常在主机防火墙、安全组或服务商端口策略。普通用户无法自行修复，需要管理员或控制面板放行。

### 11.2 让管理员配置反向代理

管理员可把已有 Web 服务中的域名转发到 `127.0.0.1:18080`。以下只是交给管理员的 Nginx 示例，不应由普通用户直接写入系统配置：

```nginx
server {
    listen 80;
    server_name publish.example.com;

    client_max_body_size 1024m;

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 720s;
        proxy_send_timeout 720s;
    }
}
```

HTTPS 证书应由现有反向代理或主机控制面板管理。用户级 Caddy 配置已关闭自动 HTTPS，避免尝试占用 80/443。上游代理的上传大小与超时必须不小于应用设置，否则大文件会在到达 FastAPI 前被拒绝或中断。

## 12. 手动理解和维护依赖

自动脚本已经完成依赖安装。以下命令用于维护和排查，不需要系统 Python 或系统 Node：

```bash
ROOT="$HOME/.local/share/content-publish"
MAMBA="$ROOT/tools/micromamba"
RUNTIME="$ROOT/runtime"
export MAMBA_ROOT_PREFIX="$ROOT/.micromamba"
```

查看用户级运行时：

```bash
"$RUNTIME/bin/python" --version
"$RUNTIME/bin/node" --version
"$RUNTIME/bin/npm" --version
"$RUNTIME/bin/postgres" --version
"$RUNTIME/bin/caddy" version
```

重新安装/校验后端依赖：

```bash
"$RUNTIME/bin/python" -m pip install -r "$ROOT/app/backend/requirements.txt"
"$RUNTIME/bin/python" -m pip check
```

重新安装并构建前端：

```bash
cd "$ROOT/app"
VITE_API_BASE_URL=/api VITE_USE_MOCK=false "$RUNTIME/bin/npm" ci
VITE_API_BASE_URL=/api VITE_USE_MOCK=false "$RUNTIME/bin/npm" run build
```

校验 Caddy 配置：

```bash
"$RUNTIME/bin/caddy" validate \
  --config "$ROOT/config/Caddyfile" \
  --adapter caddyfile
```

不要运行全局 `npm install -g`，也不要给系统 Python 执行 `pip install`。所有依赖都应留在 `$INSTALL_ROOT/runtime`。

## 13. PostgreSQL 管理

用户级 PostgreSQL 只监听回环地址，不应直接暴露到公网。默认数据库密码保存在：

```text
$HOME/.local/share/content-publish/config/postgres-password
```

连接数据库：

```bash
ROOT="$HOME/.local/share/content-publish"
export PGPASSWORD="$(cat "$ROOT/config/postgres-password")"
"$ROOT/runtime/bin/psql" \
  -h 127.0.0.1 -p 15432 \
  -U content_publish -d content_publish
```

查看数据库状态：

```bash
"$ROOT/runtime/bin/pg_ctl" -D "$ROOT/postgres/data" status
```

数据库由 Supervisor 管理时，不要单独使用 `pg_ctl stop`；应使用 `content-publishctl stop`，保证后端和数据库按统一流程停止。

## 14. 更新应用

先备份，再把新版本源码上传/拉取到 `$HOME/publish_project`。随后重复执行同一安装命令：

```bash
cd "$HOME/publish_project"
PUBLIC_URL="https://publish.example.com" \
  bash scripts/deploy-el9-nonroot.sh install
```

脚本会先正常停止旧 Supervisor，再同步代码、更新依赖、迁移数据库、构建前端并重新启动。默认保留现有 `backend/.env`、数据库、上传文件、发布文件和随机凭证。

不要在普通代码更新时使用 `FORCE_CONFIG=1`。只有确实要重建后端配置时才使用它，并提前备份原 `.env`。若必须重建，请把原 `JWT_SECRET_KEY` 作为环境变量传入，避免所有登录会话失效：

```bash
JWT_SECRET_KEY="复制原配置中的值" \
FORCE_CONFIG=1 \
PUBLIC_URL="https://new-publish.example.com" \
  bash scripts/deploy-el9-nonroot.sh install
```

## 15. 备份和恢复

### 15.1 备份数据库

```bash
ROOT="$HOME/.local/share/content-publish"
BACKUP_ROOT="$HOME/content-publish-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_ROOT"
chmod 700 "$HOME/content-publish-backups" "$BACKUP_ROOT"
export PGPASSWORD="$(cat "$ROOT/config/postgres-password")"
"$ROOT/runtime/bin/pg_dump" \
  -h 127.0.0.1 -p 15432 \
  -U content_publish -d content_publish \
  -Fc -f "$BACKUP_ROOT/database.dump"
```

### 15.2 备份配置和文件

```bash
ROOT="$HOME/.local/share/content-publish"
tar -C "$ROOT" -czf "$BACKUP_ROOT/config-and-data.tar.gz" config data
chmod 600 "$BACKUP_ROOT/database.dump" "$BACKUP_ROOT/config-and-data.tar.gz"
```

将备份复制到另一台受控主机或公司备份系统。只放在同一服务器上不能应对磁盘或实例故障。

### 15.3 恢复数据库

先停止服务，确认目标数据库正确，再执行：

```bash
ROOT="$HOME/.local/share/content-publish"
"$ROOT/bin/content-publishctl" stop
export PGPASSWORD="$(cat "$ROOT/config/postgres-password")"
"$ROOT/runtime/bin/pg_restore" \
  -h 127.0.0.1 -p 15432 \
  -U content_publish -d content_publish \
  --clean --if-exists "$HOME/content-publish-backups/时间戳/database.dump"
"$ROOT/bin/content-publishctl" start
```

`pg_restore --clean` 会覆盖目标库中的现有对象，执行前必须再次确认备份和目标数据库。

## 16. 常见故障

### 下载 Micromamba 或依赖失败

确认服务器能解析域名并访问 HTTPS：

```bash
curl -I https://micro.mamba.pm/
curl -I https://conda.anaconda.org/conda-forge/
curl -I https://pypi.org/
curl -I https://registry.npmjs.org/
```

公司网络使用代理或内网镜像时，应按公司规范设置 `HTTPS_PROXY`、npm registry、pip index 和 Micromamba 镜像。不要关闭 TLS 校验。

### 前端构建提示 `/usr/bin/env: 'node': No such file or directory`

这表示 npm 已安装，但运行 npm 时的 `PATH` 没有包含用户级 Node.js。新版脚本会自动把 `$INSTALL_ROOT/runtime/bin` 放在 `PATH` 最前面，并在构建前验证 `node` 和 npm 版本。上传新版脚本后直接重复原来的 `install` 命令即可；之前已创建的数据库和配置会被保留。

临时验证命令：

```bash
ROOT="$HOME/.local/share/content-publish"
export PATH="$ROOT/runtime/bin:$PATH"
command -v node
node --version
"$ROOT/runtime/bin/npm" --version
```

`command -v node` 应输出 `$HOME/.local/share/content-publish/runtime/bin/node`。安装失败日志中的 PostgreSQL `received fast shutdown request` 是脚本在失败后进行的正常清理，不代表数据库损坏。

### `Address already in use`

查看端口占用，并换用未占用的高端口重新部署：

```bash
ss -lntp 2>/dev/null | grep -E ':(18080|18000|15432)[[:space:]]' || true
WEB_PORT=28080 API_PORT=28000 DB_PORT=25432 \
PUBLIC_URL="http://web1138.sh.fuk1:28080" \
  bash scripts/deploy-el9-nonroot.sh install
```

### 本机健康检查正常，外网打不开

这通常不是应用故障。检查主机面板的端口开放、云安全组和反向代理；无 root 用户需要管理员处理防火墙和 80/443。

### 浏览器显示 502

先检查本机：

```bash
curl -v "http://127.0.0.1:18080/api/health"
"$HOME/.local/share/content-publish/bin/content-publishctl" status
tail -n 200 "$HOME/.local/share/content-publish/logs/backend.log"
```

若本机成功而域名失败，检查上游反向代理是否指向正确的 `127.0.0.1:18080`。如果反向代理位于另一台主机，不能使用它自己的 `127.0.0.1`，必须连接应用服务器的可达地址。

### 大文件上传出现 413 或超时

同时检查：

- 后端 `.env` 的 `MAX_UPLOAD_SIZE_MB`；
- 上游 Nginx/主机控制面板的上传上限；
- 上游代理读写超时；
- 浏览器到代理、代理到 `18080` 的连接是否稳定。

应用默认上限为 1024 MB。上游代理限制应不小于应用限制。

### SSH 退出后进程消失

主机可能启用了用户进程清理。配置用户 systemd 并让管理员开启 linger，或使用主机控制面板的守护进程功能。`nohup` 无法对抗管理员级的会话清理策略。

### `systemctl --user` 无法连接

用户会话总线或 linger 不可用。改用控制面板或 crontab，并联系管理员确认主机支持的非 root 守护方式。

### 数据库启动失败

```bash
tail -n 200 "$HOME/.local/share/content-publish/logs/postgresql.log"
tail -n 200 "$HOME/.local/share/content-publish/logs/postgresql-bootstrap.log"
```

常见原因包括端口冲突、HOME 磁盘不足、文件权限被修改、异常关机后的数据库恢复尚未完成。不要手工删除 `postmaster.pid`，除非已经确认没有任何 PostgreSQL 进程在使用该数据目录。

### 分类配置、内容检索、审核管理和内容管理同时报错

这些页面都会读取 `/api/categories`。先上传包含最新 Alembic 迁移的完整项目并重复执行 `install`；脚本会执行幂等的分类表修复迁移，并在启动前检查分类表结构：

```bash
cd "$HOME/publish_project"
PUBLIC_URL="之前部署时使用的地址" \
  bash scripts/deploy-el9-nonroot.sh install
```

不要为这次修复设置 `FORCE_CONFIG=1`。完成后检查：

```bash
ROOT="$HOME/.local/share/content-publish"
cd "$ROOT/app/backend"
"$ROOT/runtime/bin/python" -m alembic current
curl -fsS "http://127.0.0.1:18080/api/health"
```

当前迁移版本应为 `20260908_0006 (head)`，健康检查应返回 `status: ok`。如果迁移失败，查看终端中的 Alembic 原始错误以及 `$ROOT/logs/backend.log`，不要手工修改 `alembic_version`。

## 17. 官方参考

- [Micromamba 安装文档](https://mamba.readthedocs.io/en/stable/installation/micromamba-installation.html)
- [conda-forge PostgreSQL 包](https://anaconda.org/conda-forge/postgresql)
- [conda-forge Caddy 包](https://prefix.dev/channels/conda-forge/packages/caddy)
- [PostgreSQL 16 initdb 文档](https://www.postgresql.org/docs/16/app-initdb.html)
- [Caddy 命令行与配置校验](https://caddyserver.com/docs/command-line)

PostgreSQL 官方要求 `initdb` 和数据库服务由拥有数据目录的非 root 用户运行，这与本方案的用户级数据库设计一致。
