# 前端、后端、PostgreSQL 三机部署说明

本文适用于前端、后端和 PostgreSQL 分别部署在同一内网不同服务器的场景。示例按 Enterprise Linux 9、Nginx、PostgreSQL 16 编写；把示例域名、IP、账号和目录替换为实际值后再执行。

本文不会要求浏览器直接访问后端 IP。浏览器始终访问前端域名，前端 Nginx 将 `/api/` 和 `/local-published/` 同源转发到后端机，可避免生产环境 CORS、localhost 和发布 URL 指向错误机器的问题。

应用发布账号可以保持非 root。本文中只有安装系统软件、配置 PostgreSQL/Nginx、SELinux、firewalld 和 systemd 的命令需要 `sudo`，应由三台机器各自的管理员首次执行；日常上传代码、安装项目依赖和构建前端可交给普通发布账号。若三台机器都完全无法获得管理员协助，则不能自行配置 80/443、系统 Nginx、数据库监听地址或主机防火墙，需要由现有托管平台提供这些能力。

## 1. 示例拓扑与替换项

| 角色 | 示例 | 对外开放 |
|---|---|---|
| 前端机 | `10.20.30.11` / `publish.example.com` | `80/443` 给用户 |
| 后端机 | `10.20.30.12` | `8080` 仅给前端机 |
| 数据库机 | `10.20.30.13` / `db-content.internal` | `5432` 仅给后端机 |
| 办公/VPN 网段 | `10.20.30.0/24` | 可访问普通发布文件 |

在实施前确定以下变量：

```text
FRONTEND_IP=10.20.30.11
BACKEND_IP=10.20.30.12
DATABASE_IP=10.20.30.13
USER_NETWORK_CIDR=10.20.30.0/24
PUBLIC_HOST=publish.example.com
BACKEND_ROOT=/srv/content-publish/app/backend
DATA_ROOT=/srv/content-publish/data
WEB_ROOT=/usr/share/nginx/html/content-publish
```

建议为三台机器配置固定 IP 或固定内网 DNS。不要在应用配置中使用可能变化的 DHCP 地址。

请求路径如下：

```text
浏览器 https://publish.example.com/
   ├─ /                       -> 前端机 Nginx -> Vue dist
   ├─ /api/*                  -> 前端机 Nginx -> 后端机 Nginx:8080 -> FastAPI:8000
   └─ /local-published/*      -> 前端机 Nginx -> 后端机 Nginx:8080 -> 后端发布目录

后端 FastAPI -> PostgreSQL 数据库机:5432
```

## 2. 网络与安全策略

只开放实际需要的方向：

| 来源 | 目标 | 端口 | 用途 |
|---|---|---:|---|
| 用户办公网/VPN/负载均衡器 | 前端机 | 80、443 | 页面、API 和内容入口 |
| 前端机 `10.20.30.11` | 后端机 | 8080 | Nginx 内网网关 |
| 后端机 `10.20.30.12` | 数据库机 | 5432 | PostgreSQL |
| 后端机 | Internet | 443 | GitHub、OneDrive、Dropbox、Instagram API |
| Internet | 前端机 | 443 | 仅在使用公网域名或 Instagram 拉取视频时需要 |

禁止的连接：

- 前端机和用户终端不能直接连接 PostgreSQL；
- 用户不能直接连接 FastAPI 的 `8000`；
- 数据库 `5432` 不能向整个局域网或公网开放；
- 后端 Nginx `8080` 只允许前端机 IP。

如果服务器有 firewalld，还应在云安全组、交换机 ACL 或主机防火墙中实施同样规则，不能只依赖 Nginx `allow/deny`。

## 3. 数据库机部署 PostgreSQL 16

### 3.1 安装和初始化

按公司的 PostgreSQL 16 软件源安装。以 RHEL/EL9 的 PGDG 包为例，服务名可能是 `postgresql-16`：

```bash
sudo dnf install -y postgresql16-server postgresql16
sudo /usr/pgsql-16/bin/postgresql-16-setup initdb
sudo systemctl enable --now postgresql-16
```

如果使用系统 AppStream 或公司镜像，以实际二进制路径和服务名为准。用以下 SQL确认配置文件位置：

```bash
sudo -u postgres psql -Atc 'show config_file'
sudo -u postgres psql -Atc 'show hba_file'
```

### 3.2 创建账号和数据库

生成强密码后执行；不要把示例密码原样使用：

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE content_publish LOGIN PASSWORD '替换为强密码';
CREATE DATABASE content_publish OWNER content_publish ENCODING 'UTF8';

-- 只有确实要在此环境执行 pytest 时才创建，且必须与生产库隔离。
CREATE ROLE content_publish_test LOGIN PASSWORD '替换为另一强密码';
CREATE DATABASE content_publish_test OWNER content_publish_test ENCODING 'UTF8';
```

项目测试会清理测试库中的业务表，绝不能把 `TEST_DATABASE_URL` 指向 `content_publish` 生产库。

### 3.3 监听内网地址

在 `postgresql.conf` 中配置实际数据库 IP，不建议为了方便使用 `*`：

```conf
listen_addresses = '10.20.30.13'
port = 5432
password_encryption = 'scram-sha-256'
```

在 `pg_hba.conf` 前部加入精确的后端机 `/32` 规则：

```conf
# TYPE  DATABASE              USER                  ADDRESS          METHOD
host    content_publish       content_publish       10.20.30.12/32  scram-sha-256
host    content_publish_test  content_publish_test  10.20.30.12/32  scram-sha-256
```

`pg_hba.conf` 从上到下匹配，避免在这些规则前放置允许整个网段的宽泛规则。更高安全要求下应启用 PostgreSQL TLS，把规则改成 `hostssl`，并在后端连接串使用 `sslmode=verify-full&sslrootcert=/证书路径/ca.crt`。

重启并检查：

```bash
sudo systemctl restart postgresql-16
sudo systemctl status postgresql-16 --no-pager
sudo ss -lntp | grep ':5432'
```

firewalld 仅允许后端机：

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.20.30.12/32" port protocol="tcp" port="5432" accept'
sudo firewall-cmd --reload
```

## 4. 后端机部署 FastAPI

### 4.1 安装代码与运行环境

管理员先安装后端机的基础软件：

```bash
sudo dnf install -y git rsync curl gcc nginx postgresql policycoreutils-python-utils
python3.12 --version
```

后端要求 Python 3.12。若系统仓库没有 `python3.12`，应使用公司批准的软件源或用户级 Micromamba 安装，不要用系统 Python 强行创建不兼容的环境。`postgresql` 在后端机只安装客户端，不初始化数据库服务。

以下使用专用系统账号；项目目录可按公司标准调整。这组创建账号和目录的命令仅需管理员首次执行：

```bash
sudo useradd --system --home-dir /srv/content-publish --shell /sbin/nologin contentpub
sudo install -d -m 0750 -o contentpub -g contentpub /srv/content-publish/app
sudo install -d -m 0750 -o contentpub -g contentpub /srv/content-publish/data/{source,preview,build}
sudo install -d -m 0755 -o contentpub -g contentpub /srv/content-publish/data/published
```

把项目的 `backend/` 同步到 `/srv/content-publish/app/backend/`，然后安装 Python 依赖：

```bash
cd /srv/content-publish/app/backend
sudo -u contentpub python3.12 -m venv .venv
sudo -u contentpub .venv/bin/python -m pip install --upgrade pip
sudo -u contentpub .venv/bin/python -m pip install -r requirements.txt
```

### 4.2 后端 `.env`

创建 `/srv/content-publish/app/backend/.env`：

```dotenv
APP_NAME=Internal Content Publish Platform
APP_ENV=production
DEBUG=false

DATABASE_URL=postgresql+psycopg://content_publish:URL编码后的密码@10.20.30.13:5432/content_publish
TEST_DATABASE_URL=postgresql+psycopg://content_publish_test:URL编码后的独立密码@10.20.30.13:5432/content_publish_test

JWT_SECRET_KEY=替换为至少32字节的随机密钥
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480

SOURCE_STORAGE_ROOT=/srv/content-publish/data/source
PREVIEW_STORAGE_ROOT=/srv/content-publish/data/preview
BUILD_STORAGE_ROOT=/srv/content-publish/data/build
LOCAL_PUBLISHED_ROOT=/srv/content-publish/data/published
LOCAL_PUBLISHED_BASE_URL=/local-published
MAX_UPLOAD_SIZE_MB=1024

PUBLISH_CONNECTION_TIMEOUT_SECONDS=30
PUBLISH_OPERATION_TIMEOUT_SECONDS=600
CORS_ORIGINS=https://publish.example.com
DB_CONNECT_TIMEOUT_SECONDS=5
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

数据库密码中的 `@`、`:`、`/`、`#`、`%` 等字符必须进行 URL 编码。可以在安全终端本地计算：

```bash
python3 -c 'from urllib.parse import quote; print(quote(input("Password: "), safe=""))'
```

保持配置权限：

```bash
sudo chown contentpub:contentpub /srv/content-publish/app/backend/.env
sudo chmod 600 /srv/content-publish/app/backend/.env
```

### 4.3 验证数据库并迁移

从后端机验证网络和账号：

```bash
psql 'postgresql://content_publish@10.20.30.13:5432/content_publish' -c 'select current_database(), current_user;'
```

执行迁移：

```bash
cd /srv/content-publish/app/backend
sudo -u contentpub .venv/bin/alembic upgrade head
sudo -u contentpub .venv/bin/alembic current
```

生产数据初始化只在首次部署执行一次：

```bash
sudo -u contentpub .venv/bin/python scripts/seed.py
```

首次登录后立即修改 Seed 默认密码。已有环境升级时不要反复依赖 Seed 管理账号。

### 4.4 systemd 服务

创建 `/etc/systemd/system/content-publish.service`：

```ini
[Unit]
Description=Content Publish FastAPI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=contentpub
Group=contentpub
WorkingDirectory=/srv/content-publish/app/backend
ExecStart=/srv/content-publish/app/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2 --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=3
TimeoutStopSec=30
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/srv/content-publish/data

[Install]
WantedBy=multi-user.target
```

启动并本机检查：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now content-publish
curl -fsS http://127.0.0.1:8000/api/health
sudo journalctl -u content-publish -n 100 --no-pager
```

FastAPI 只监听回环地址；跨机器流量由后端 Nginx 接收。

## 5. 后端机 Nginx

后端 Nginx 有两个职责：

1. 将 `/api/` 转发给本机 `127.0.0.1:8000`；
2. 从后端磁盘只读提供 `/local-published/`。

配置模板：[backend-content-publish.conf.example](../deploy/nginx/backend-content-publish.conf.example)。复制并替换 IP、目录：

```bash
sudo dnf install -y nginx policycoreutils-python-utils
sudo cp deploy/nginx/backend-content-publish.conf.example /etc/nginx/conf.d/content-publish-backend.conf
sudo nginx -t
sudo systemctl enable --now nginx
```

项目代码不在当前目录时，先把模板复制到服务器再执行 `cp`。

EL9 启用 SELinux 时允许 Nginx 连接本机 FastAPI，并标记发布目录：

```bash
sudo setsebool -P httpd_can_network_connect 1
sudo semanage fcontext -a -t httpd_sys_content_t '/srv/content-publish/data/published(/.*)?'
sudo restorecon -RF /srv/content-publish/data/published
```

只开放前端机到 `8080`：

```bash
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.20.30.11/32" port protocol="tcp" port="8080" accept'
sudo firewall-cmd --reload
```

不要开放 `8000`。在前端机上验证：

```bash
curl -fsS http://10.20.30.12:8080/api/health
```

在其他机器上访问 `8080` 应被防火墙或 Nginx 拒绝。

## 6. 前端机构建 Vue

管理员先安装 Nginx 和基础命令；构建机准备 Node.js 22 LTS（最低 20.19）及 npm 10：

```bash
sudo dnf install -y nginx git rsync curl policycoreutils-python-utils
node --version
npm --version
```

若系统仓库的 Node.js 版本过低，应使用公司批准的 Node.js 软件源或普通用户级版本管理工具安装。只把构建后的 `dist/` 交给 Nginx，前端机不需要 Python，也不需要连接 PostgreSQL。

前端构建必须使用相对 API 地址，不能写后端 IP：

```bash
cd /opt/content-publish-source
npm ci
VITE_API_BASE_URL=/api VITE_USE_MOCK=false npm run build
sudo install -d -m 0755 /usr/share/nginx/html/content-publish
sudo rsync -a --delete dist/ /usr/share/nginx/html/content-publish/
```

最终生成的 JavaScript 只请求当前域名的 `/api`。以后更换后端 IP，只改前端 Nginx upstream，不需要重新构建 Vue。

## 7. 前端机 Nginx

前端 Nginx 负责：

- 终止正式域名 HTTPS；
- 提供 Vue `dist`；
- 把 `/api/` 原路径转发到后端机；
- 把 `/local-published/` 转发到后端发布目录；
- 让普通发布内容只对办公/VPN 网段开放；
- 让随机、短时的 `/_instagram/` 视频地址可以被 Meta 下载。

配置模板：[frontend-content-publish.conf.example](../deploy/nginx/frontend-content-publish.conf.example)。复制后至少替换：

- `publish.example.com`；
- 后端 IP `10.20.30.12`；
- 办公/VPN CIDR `10.20.30.0/24`；
- TLS 证书和私钥路径；
- Vue `WEB_ROOT`。

安装、验证并加载：

```bash
sudo dnf install -y nginx policycoreutils-python-utils
sudo cp deploy/nginx/frontend-content-publish.conf.example /etc/nginx/conf.d/content-publish-frontend.conf
sudo setsebool -P httpd_can_network_connect 1
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

`proxy_pass http://content_publish_backend_gateway;` 后面故意没有 URI 和结尾 `/`，这样 `/api/health` 仍以 `/api/health` 到达后端。不要随意改成会去掉 `/api` 的写法。

`client_max_body_size` 必须略大于后端 `MAX_UPLOAD_SIZE_MB`；Nginx 默认值很小，大文件超限会在到达 FastAPI 前返回 413。发布或审核接口可能等待第三方平台处理，两个 Nginx 的 `proxy_read_timeout` 都必须大于后端 `PUBLISH_OPERATION_TIMEOUT_SECONDS`。

如果前端机位于负载均衡器后面，`allow/deny` 看到的可能是负载均衡器 IP。此时应按公司网络方案正确配置 Nginx Real IP 模块和受信任的 `set_real_ip_from`，不要直接信任任意来源的 `X-Forwarded-For`。

## 8. Local 发布目标配置

Local 发布文件实际写在后端机，不能填写前端机路径。例如管理部发布区：

```text
服务器发布根目录：/srv/content-publish/data/published/management
URL 根地址：/local-published/management/
```

单文件会得到类似地址：

```text
https://publish.example.com/local-published/management/src-montage.png
```

多文件/页面内容仍按目录和 `index.html` 访问。不要把 URL 写成后端私网 IP；统一使用站点相对 URL，浏览器会自动使用前端正式域名。

### Instagram 发布目标

Instagram 的 `media_base_url` 应填写：

```text
https://publish.example.com/local-published/_instagram/
```

该地址必须能从公网通过有效 HTTPS 下载，不能限制为办公网段。前端模板已把更具体的 `/_instagram/` location 放在普通发布目录之前。临时路径随机生成并在发布结束后删除，但正式环境仍应监控访问日志和异常残留。

如果系统完全不发布 Instagram，可以删除前端配置中公开的 `/_instagram/` location，让整个 `/local-published/` 只对内网开放。

## 9. PostgreSQL TLS 连接（推荐）

同一网段并不等于链路可信。生产环境推荐给数据库配置由公司 CA 签发、包含 `db-content.internal` 的服务端证书：

```conf
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/pki/tls/certs/db-content.internal.crt'
ssl_key_file = '/etc/pki/tls/private/db-content.internal.key'
ssl_ca_file = '/etc/pki/ca-trust/source/anchors/company-ca.crt'
```

`pg_hba.conf` 改为：

```conf
hostssl content_publish content_publish 10.20.30.12/32 scram-sha-256
```

后端连接串使用内网 DNS 名称而不是证书不包含的 IP：

```dotenv
DATABASE_URL=postgresql+psycopg://content_publish:URL编码密码@db-content.internal:5432/content_publish?sslmode=verify-full&sslrootcert=/etc/pki/ca-trust/source/anchors/company-ca.crt
```

不要用 `sslmode=disable` 或关闭证书校验来绕过证书错误。

## 10. 端到端验收

### 10.1 数据库链路

仅在后端机执行：

```bash
psql 'postgresql://content_publish@10.20.30.13:5432/content_publish' -c 'select now();'
```

该命令会安全地交互询问数据库密码。这里不能直接把 SQLAlchemy 使用的 `postgresql+psycopg://...` 原样传给 `psql`。

前端机连接数据库端口应失败：

```bash
nc -vz 10.20.30.13 5432
```

### 10.2 后端链路

后端机：

```bash
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS http://10.20.30.12:8080/api/health
```

前端机：

```bash
curl -fsS http://10.20.30.12:8080/api/health
```

### 10.3 用户入口

从用户电脑执行：

```bash
curl -I https://publish.example.com/
curl -fsS https://publish.example.com/api/health
```

登录后完成：

1. 新建一条小文件内容并发布到 Local 目标；
2. 在内容详情点击“打开内容”；
3. 确认 URL 域名始终是 `publish.example.com`；
4. 确认刷新 `/contents/数字ID` 等前端路由不会 404；
5. 上传接近上限的测试文件，确认不会返回 413；
6. 从非办公网访问普通 `/local-published/` 应被拒绝；
7. 使用 Instagram 时，从公网验证临时 URL 可下载后再发布测试视频。

### 10.4 日志位置

```bash
# 前端机
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log

# 后端机
sudo journalctl -u content-publish -f
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log

# 数据库机
sudo journalctl -u postgresql-16 -f
```

## 11. 更新发布顺序

建议每次发布按以下顺序：

1. 备份 PostgreSQL；
2. 后端机同步新代码并安装依赖；
3. 后端机执行 `alembic upgrade head`；
4. 重启 FastAPI 并确认本机 `/api/health`；
5. 前端机构建并原子替换 `dist`；
6. 两台 Nginx 分别执行 `nginx -t` 后 reload；
7. 从用户入口完成登录、发布、打开内容和日志检查。

Vue 前端纯静态文件可以先同步到带版本号的目录，再用软链接切换，以便快速回滚。数据库迁移前必须先确认备份可恢复；不要使用 `git reset --hard` 或直接删除数据目录回滚。

## 12. 常见问题

### 页面正常但 API 返回 502

- 在前端机测试 `curl http://10.20.30.12:8080/api/health`；
- 检查后端 firewalld 和 Nginx `allow` 是否填写了正确的前端 IP；
- EL9 检查前端 Nginx 是否已启用 `httpd_can_network_connect`；
- 后端机检查 FastAPI 是否监听 `127.0.0.1:8000`。

### API 返回 `{"detail":"Not Found"}`

检查 `proxy_pass` 是否保留了 `/api` 前缀。使用本文模板时请求 `/api/health` 会原样到达后端，不应改写为 `/health`。

### 发布成功但文件 URL 404

- Local 目标的 `publish_root` 必须位于后端 `LOCAL_PUBLISHED_ROOT` 对应子目录；
- URL 根地址应是 `/local-published/对应子目录/`；
- 后端 Nginx 的 `alias` 必须指向同一个 `LOCAL_PUBLISHED_ROOT`；
- 前端 Nginx 必须把 `/local-published/` 原路径转发给后端；
- 检查目录执行权限、SELinux 标签和文件名大小写。

### 上传返回 413

前、后两台 Nginx 都要设置足够的 `client_max_body_size`，并且后端 `MAX_UPLOAD_SIZE_MB` 也要允许该文件。

### 发布等待约 60 秒后提示连接失败

Nginx 默认代理读取超时可能短于第三方发布任务。前、后两台均按模板设置 `proxy_read_timeout 720s`、`proxy_send_timeout 720s`，并保证它们大于 `PUBLISH_OPERATION_TIMEOUT_SECONDS`。

### 数据库连接被拒绝

- 数据库 `listen_addresses` 是否为数据库机内网 IP；
- `pg_hba.conf` 是否有后端机 `/32` 且顺序正确；
- 数据库机防火墙是否只允许后端 IP；
- 连接串密码是否做过 URL 编码；
- 使用 TLS 时，数据库 DNS 名称是否包含在证书 SAN 中。

## 13. 权限边界提醒

当前系统的分类权限控制决定用户能否在页面和 API 中发现、读取内容详情，但 Nginx 静态文件 URL 本身不执行用户级数据库权限判断。`allow/deny` 只能做到网络级限制，不能区分具体登录用户。

如果公司要求“即使拿到 URL，也必须再次核验用户、部门和分类权限”，需要把发布文件改为后端鉴权下载、签名短链接，或增加 Nginx `auth_request` 对接接口；在实现该能力前，不应把普通 `/local-published/` 开放到公网。

## 14. 官方参考

- [Nginx 反向代理模块](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Nginx 请求体大小配置](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size)
- [PostgreSQL 16 连接设置](https://www.postgresql.org/docs/16/runtime-config-connection.html)
- [PostgreSQL 16 `pg_hba.conf`](https://www.postgresql.org/docs/16/auth-pg-hba-conf.html)
- [RHEL 9 Nginx 与反向代理](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html-single/deploying_web_servers_and_reverse_proxies/index)
