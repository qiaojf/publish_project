# 内容自动发布平台：Enterprise Linux 9 服务器部署指南

> 本文需要 `root` 或 `sudo` 权限。无法取得 root 权限时，请改用 [`SERVER_DEPLOYMENT_NON_ROOT_README.md`](SERVER_DEPLOYMENT_NON_ROOT_README.md) 和 `scripts/deploy-el9-nonroot.sh`。

本文面向以下服务器：

```text
Linux web1138.sh.fuk1 5.14.0-503.40.1.ghostlock1.el9_5.x86_64 x86_64 GNU/Linux
```

内核标识表明它属于 Enterprise Linux 9.5 兼容环境，但仅凭内核不能确定具体发行版。部署前必须运行 `cat /etc/os-release`，确认系统使用 `dnf`，且 `VERSION_ID` 主版本为 `9`。自动部署脚本支持 RHEL 9、Rocky Linux 9、AlmaLinux 9、Oracle Linux 9，以及提供兼容 AppStream 的 EL9 衍生系统。

## 1. 部署架构

生产环境采用单机部署：

```text
浏览器
  |
  v
Nginx :80/:443
  |-- /              -> Vue dist 静态文件
  |-- /api/          -> FastAPI 127.0.0.1:8000
  `-- /published/    -> 发布内容目录

FastAPI systemd 服务
  |
  `-- PostgreSQL 16 127.0.0.1:5432
```

默认目录：

```text
/opt/content-publish                    程序目录
/opt/content-publish/backend/.venv      Python 虚拟环境
/opt/content-publish/backend/.env       后端生产配置和第三方凭证
/srv/content-publish/source             上传的源文件
/srv/content-publish/preview            预览文件
/srv/content-publish/build              发布前构建产物
/srv/content-publish/published          Local 目标的正式发布内容
/usr/share/nginx/html/content-publish   Vue 生产构建文件
```

公网或内网只需要开放 `80/443`。不要开放 PostgreSQL `5432` 和 FastAPI `8000`。

## 2. 部署前准备

建议最低资源：

- 2 核 CPU、4 GB 内存。
- 系统盘至少预留 10 GB；文件较多时，将 `/srv/content-publish` 放在独立数据盘。
- 可用的 `root` 或 `sudo` 权限。
- 服务器可以访问系统软件仓库、PyPI 和 npm registry。
- 使用正式域名时，先把域名 A/AAAA 记录指向服务器。
- 防火墙或云安全组允许 SSH、HTTP；配置 HTTPS 后允许 HTTPS。

检查系统：

```bash
cat /etc/os-release
uname -a
command -v dnf
df -h
free -h
```

后端必须使用 Python 3.11 或更高版本，因为代码使用了 `enum.StrEnum`。前端 Vite 7 需要 Node.js 20.19+ 或 22.12+，本文统一使用 Node.js 22。数据库使用 PostgreSQL 16。

## 3. 上传项目代码

自动脚本不会从未知仓库下载代码。先将完整项目上传到服务器，例如：

```bash
rsync -av --exclude node_modules --exclude backend/.venv --exclude .git \
  --exclude .env --exclude .env.local --exclude backend/.env --exclude .ssh \
  --exclude 'id_rsa*' --exclude 'id_ed25519*' \
  --exclude '*.pem' --exclude '*.key' --exclude '*.p12' --exclude '*.pfx' \
  ./publish_project/ root@web1138.sh.fuk1:/root/publish_project/
```

也可以在服务器上从公司的 Git 仓库克隆：

```bash
git clone <公司仓库地址> /root/publish_project
cd /root/publish_project
```

不要上传本地 `.env`、`.env.local`、Token、私钥、数据库文件或 `solution_qiao.pem`。自动脚本复制代码时也会排除常见私钥文件。

## 4. 推荐：自动部署

脚本位置：`scripts/deploy-el9.sh`。

### 4.1 使用服务器主机名部署 HTTP

```bash
cd /root/publish_project
chmod +x scripts/deploy-el9.sh
sudo env PUBLIC_URL=http://web1138.sh.fuk1 \
  bash scripts/deploy-el9.sh
```

### 4.2 使用正式域名

```bash
sudo env PUBLIC_URL=https://publish.example.com \
  bash scripts/deploy-el9.sh
```

如果本机 Nginx 直接终止 HTTPS，应先用 `http://publish.example.com` 完成部署和验证，再按第 14 节配置证书，并把后端 `.env` 中的公开 URL 改成 HTTPS。若 HTTPS 在外部负载均衡器上终止，则可以直接使用 `https://`。

### 4.3 同时执行后端测试

```bash
sudo env PUBLIC_URL=http://web1138.sh.fuk1 RUN_TESTS=1 \
  bash scripts/deploy-el9.sh
```

启用后脚本会另外创建 `content_publish_test`。测试夹具只允许操作这个隔离测试库，不会清理生产库。

### 4.4 自定义程序和数据根目录

```bash
sudo env \
  PUBLIC_URL=https://publish.example.com \
  APP_ROOT=/data/apps/content-publish \
  DATA_ROOT=/data/content-publish \
  WEB_ROOT=/var/www/content-publish \
  bash scripts/deploy-el9.sh
```

重要环境变量：

| 变量 | 默认值 | 作用 |
|---|---|---|
| `PUBLIC_URL` | `http://$(hostname -f)` | 用户访问的协议、域名或 IP，不要带路径 |
| `APP_ROOT` | `/opt/content-publish` | 程序、前端源码和 Python 虚拟环境 |
| `DATA_ROOT` | `/srv/content-publish` | 源文件、预览、构建和 Local 发布文件 |
| `WEB_ROOT` | `/usr/share/nginx/html/content-publish` | Nginx 前端静态目录 |
| `APP_USER` | `contentpub` | systemd 服务用户 |
| `DB_NAME` | `content_publish` | 生产数据库名 |
| `DB_USER` | `content_publish` | 数据库应用账号 |
| `DB_PASSWORD` | 首次随机生成 | 数据库密码；也可以主动指定 |
| `INITIAL_ADMIN_PASSWORD` | 首次随机生成 | 初始管理员密码 |
| `INITIAL_EMPLOYEE_PASSWORD` | 首次随机生成 | 初始员工密码 |
| `MAX_UPLOAD_SIZE_MB` | `1024` | 后端上传总大小限制；如服务器磁盘较小可调低 |
| `UVICORN_WORKERS` | `2` | FastAPI worker 数量 |
| `RUN_TESTS` | `0` | 设为 `1` 时创建测试库并运行 pytest |
| `FORCE_CONFIG` | `0` | 设为 `1` 时重新生成 `backend/.env`，谨慎使用 |

脚本会安装系统软件、初始化 PostgreSQL、创建服务账号和数据库、安装前后端依赖、执行 Alembic 和 Seed、构建 Vue、生成 systemd/Nginx/SELinux/firewalld 配置，并检查 `/api/health`。

首次创建账号时，脚本最后会显示随机生成的 `admin` 和 `employee` 密码。密码不会写入 `backend/.env`。立即保存到公司的密码管理器；账号已经存在时，重复运行脚本不会覆盖密码。

## 5. 手动安装系统依赖

### 5.1 Python 3.11

```bash
sudo dnf install -y \
  python3.11 python3.11-pip python3.11-devel \
  gcc gcc-c++ make libffi-devel openssl-devel
python3.11 --version
```

EL9 默认的无版本 `python` 通常仍指向 Python 3.9，因此后续必须明确使用 `python3.11`。不要用 root 身份把 pip 包装进系统 Python。

### 5.2 Node.js 22 与 npm

```bash
sudo dnf module reset -y nodejs
sudo dnf module enable -y nodejs:22
sudo dnf install -y nodejs
node --version
npm --version
```

如果发行版没有 `nodejs:22` 模块，先运行 `sudo dnf module list nodejs`。不要继续使用 Node.js 18 或早期 Node.js 20，否则 Vite 7 会拒绝构建。

### 5.3 Nginx 和工具

```bash
sudo dnf install -y nginx curl git rsync openssl policycoreutils-python-utils
sudo systemctl enable nginx
nginx -v
```

## 6. 安装 PostgreSQL 16

EL9.5 AppStream 安装方法：

```bash
sudo dnf module reset -y postgresql
sudo dnf module enable -y postgresql:16
sudo dnf install -y postgresql-server postgresql-contrib
```

初始化并启动：

```bash
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql.service
sudo -u postgres pg_isready
sudo systemctl status postgresql --no-pager
```

`postgresql-setup --initdb` 只在第一次、且 `/var/lib/pgsql/data/PG_VERSION` 不存在时执行。不要对已有数据库目录重复初始化。

创建账号和数据库：

```bash
sudo -u postgres psql
```

```sql
CREATE ROLE content_publish LOGIN PASSWORD '替换为强密码';
CREATE DATABASE content_publish OWNER content_publish;
\q
```

如需测试库：

```bash
sudo -u postgres createdb -O content_publish content_publish_test
```

验证密码连接：

```bash
PGPASSWORD='数据库密码' psql \
  -h 127.0.0.1 -U content_publish -d content_publish \
  -c 'select current_database(), current_user;'
```

应用和数据库在同一服务器时，不要改成 `0.0.0.0` 监听，也不要开放 5432。

## 7. 创建服务账号和目录

```bash
sudo groupadd --system contentpub
sudo useradd --system --gid contentpub \
  --home-dir /opt/content-publish --shell /sbin/nologin contentpub
sudo install -d -m 0750 -o contentpub -g contentpub /opt/content-publish
sudo install -d -m 2770 -o contentpub -g contentpub \
  /srv/content-publish/source \
  /srv/content-publish/preview \
  /srv/content-publish/build \
  /srv/content-publish/published
sudo usermod -a -G contentpub nginx
```

复制代码并调整权限：

```bash
sudo rsync -a --exclude .git --exclude node_modules --exclude backend/.venv \
  --exclude .env --exclude .env.local --exclude backend/.env --exclude .ssh \
  --exclude 'id_rsa*' --exclude 'id_ed25519*' \
  --exclude '*.pem' --exclude '*.key' --exclude '*.p12' --exclude '*.pfx' \
  /root/publish_project/ /opt/content-publish/
sudo chown -R contentpub:contentpub /opt/content-publish
```

## 8. 后端依赖与配置

### 8.1 Python 虚拟环境

```bash
sudo -u contentpub python3.11 -m venv /opt/content-publish/backend/.venv
sudo -u contentpub /opt/content-publish/backend/.venv/bin/python \
  -m pip install --upgrade pip setuptools wheel
sudo -u contentpub /opt/content-publish/backend/.venv/bin/python \
  -m pip install -r /opt/content-publish/backend/requirements.txt
sudo -u contentpub /opt/content-publish/backend/.venv/bin/python -m pip check
```

主要依赖包括 FastAPI、Uvicorn、SQLAlchemy 2、psycopg 3、Alembic、Pydantic 2、JWT、Argon2、httpx、Paramiko 和 truststore。

### 8.2 `backend/.env`

数据库密码含 `@`、`:`、`/`、`%` 等字符时必须 URL 编码；自动脚本会处理。

```env
APP_NAME=Internal Content Publish Platform
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://content_publish:URL编码后的密码@127.0.0.1:5432/content_publish
TEST_DATABASE_URL=postgresql+psycopg://content_publish:URL编码后的密码@127.0.0.1:5432/content_publish_test
JWT_SECRET_KEY=至少48字节的随机字符串
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
SOURCE_STORAGE_ROOT=/srv/content-publish/source
PREVIEW_STORAGE_ROOT=/srv/content-publish/preview
BUILD_STORAGE_ROOT=/srv/content-publish/build
LOCAL_PUBLISHED_ROOT=/srv/content-publish/published
LOCAL_PUBLISHED_BASE_URL=https://publish.example.com/published
MAX_UPLOAD_SIZE_MB=1024
PUBLISH_CONNECTION_TIMEOUT_SECONDS=30
PUBLISH_OPERATION_TIMEOUT_SECONDS=600
CORS_ORIGINS=https://publish.example.com
DB_CONNECT_TIMEOUT_SECONDS=5
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

生成 Secret 并保护文件：

```bash
openssl rand -hex 48
sudo chown contentpub:contentpub /opt/content-publish/backend/.env
sudo chmod 600 /opt/content-publish/backend/.env
```

第三方发布凭证放在这个文件或 systemd 进程环境中：

```env
PUBLISH_CREDENTIAL_GITHUB_COMPANY_PAGES_TOKEN=...
PUBLISH_CREDENTIAL_ONEDRIVE_COMPANY_CLIENT_SECRET=...
PUBLISH_CREDENTIAL_DROPBOX_COMPANY_TOKEN=...
PUBLISH_CREDENTIAL_SFTP_INTERNAL_PASSWORD=...
```

例如 `credential_ref=github_company_pages` 会读取 `PUBLISH_CREDENTIAL_GITHUB_COMPANY_PAGES_TOKEN`。不要把 Secret 填进发布目标 config。修改 `.env` 后运行 `sudo systemctl restart content-publish`。

## 9. 前端依赖、配置和构建

生产环境使用同源 `/api`：

```bash
cd /opt/content-publish
sudo -u contentpub env VITE_API_BASE_URL=/api VITE_USE_MOCK=false npm ci
sudo -u contentpub env VITE_API_BASE_URL=/api VITE_USE_MOCK=false npm run build
```

也可以创建 `.env.production`：

```env
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
```

`npm ci` 严格使用 `package-lock.json`。部署构建结果：

```bash
sudo install -d -m 0755 /usr/share/nginx/html/content-publish
sudo rsync -a --delete /opt/content-publish/dist/ \
  /usr/share/nginx/html/content-publish/
```

生产环境不运行 `npm run dev`，也不开放 5173。

## 10. Migration 和初始化数据

```bash
cd /opt/content-publish/backend
sudo -u contentpub .venv/bin/python -m alembic upgrade head
sudo -u contentpub env \
  SEED_ADMIN_PASSWORD='管理员强密码' \
  SEED_EMPLOYEE_PASSWORD='员工强密码' \
  .venv/bin/python scripts/seed.py
sudo -u contentpub .venv/bin/python -m alembic current
sudo -u contentpub .venv/bin/python -m alembic check
```

Seed 是幂等的，只创建不存在的账号和目标，不覆盖已有密码。生产环境不要使用 `admin123`、`employee123`。

## 11. systemd 配置

自动脚本生成 `/etc/systemd/system/content-publish.service`。常用命令：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now content-publish
sudo systemctl restart content-publish
sudo systemctl status content-publish --no-pager
sudo journalctl -u content-publish -n 100 --no-pager
sudo journalctl -u content-publish -f
```

FastAPI 只监听 `127.0.0.1:8000`，外部请求统一经过 Nginx。

## 12. Nginx、SELinux 和防火墙

自动脚本生成 `/etc/nginx/conf.d/content-publish.conf`。检查：

```bash
sudo nginx -t
sudo systemctl enable --now nginx
sudo systemctl reload nginx
```

SELinux：

```bash
sudo setsebool -P httpd_can_network_connect 1
sudo semanage fcontext -a -t httpd_sys_content_t \
  '/srv/content-publish/published(/.*)?'
sudo restorecon -RF /srv/content-publish/published
```

自定义 `DATA_ROOT` 时替换实际路径。firewalld：

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --list-services
```

## 13. 修改服务器根目录

系统有两类根目录。

### 13.1 全局存储根目录

在 `backend/.env` 修改：

```env
SOURCE_STORAGE_ROOT=/data/content-publish/source
PREVIEW_STORAGE_ROOT=/data/content-publish/preview
BUILD_STORAGE_ROOT=/data/content-publish/build
LOCAL_PUBLISHED_ROOT=/data/content-publish/published
LOCAL_PUBLISHED_BASE_URL=https://publish.example.com/published
```

创建目录：

```bash
sudo install -d -m 2770 -o contentpub -g contentpub \
  /data/content-publish/source \
  /data/content-publish/preview \
  /data/content-publish/build \
  /data/content-publish/published
sudo usermod -a -G contentpub nginx
```

同步修改 Nginx：

```nginx
location /published/ {
    alias /data/content-publish/published/;
    index index.html;
    autoindex off;
}
```

更新 SELinux 并重启：

```bash
sudo semanage fcontext -a -t httpd_sys_content_t \
  '/data/content-publish/published(/.*)?'
sudo restorecon -RF /data/content-publish/published
sudo nginx -t
sudo systemctl restart content-publish nginx
```

### 13.2 每个 Local 发布目标的目录

管理员进入“发布配置”，编辑目标。例如 HTML：

```text
服务器发布根目录：/srv/content-publish/published/html
URL 根地址：https://publish.example.com/published/html/
```

PDF：

```text
服务器发布根目录：/srv/content-publish/published/pdf
URL 根地址：https://publish.example.com/published/pdf/
```

注意：

- `服务器发布根目录` 是 FastAPI 写入文件的绝对 Linux 路径。
- `URL 根地址` 是浏览器访问同一目录的地址。
- 两者末级目录必须对应，否则会“发布成功但 URL 404”。
- 目录必须归 `contentpub` 所有。
- 修改后先“测试连接”，再发布测试内容。

迁移已有发布文件时：

```bash
sudo systemctl stop content-publish
sudo rsync -aHAX /srv/content-publish/ /data/content-publish/
sudo chown -R contentpub:contentpub /data/content-publish
sudo systemctl start content-publish
```

确认新路径正常后再处理旧目录，不要提前删除旧数据。

## 14. HTTPS（可选）

使用组织证书，或在公司策略允许 Let's Encrypt 时：

```bash
sudo dnf install -y epel-release
sudo dnf install -y certbot python3-certbot-nginx
sudo certbot --nginx -d publish.example.com
sudo certbot renew --dry-run
```

必须先确保域名解析正确、80/443 可访问且公司安全策略允许。完成后把 `CORS_ORIGINS`、`LOCAL_PUBLISHED_BASE_URL` 和管理页面已有 Local 目标 URL 改为 HTTPS。

## 15. 部署验收

```bash
sudo systemctl status postgresql content-publish nginx --no-pager
sudo nginx -t
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS -H 'Host: publish.example.com' http://127.0.0.1/api/health
```

预期：

```json
{"success":true,"data":{"status":"ok"},"message":""}
```

浏览器验收：登录管理员，测试发布目标，上传 HTML/PDF，完成提交和审核发布，确认“打开内容”和“在新窗口打开”均可访问，并检查发布记录和系统日志。

## 16. 更新部署

先备份，再更新代码并用与首次相同的变量重跑脚本：

```bash
cd /root/publish_project
git pull
sudo env \
  PUBLIC_URL=https://publish.example.com \
  APP_ROOT=/opt/content-publish \
  DATA_ROOT=/srv/content-publish \
  bash scripts/deploy-el9.sh
```

已有 `backend/.env` 默认保留。只有明确需要重新生成配置时才使用 `FORCE_CONFIG=1`。

## 17. 备份

```bash
sudo install -d -m 0700 /var/backups/content-publish
sudo -u postgres pg_dump -Fc content_publish \
  > /var/backups/content-publish/content_publish_$(date +%F_%H%M%S).dump
sudo tar -C /srv -czf \
  /var/backups/content-publish/files_$(date +%F_%H%M%S).tar.gz \
  content-publish
```

至少备份数据库、`source/`、`published/` 和加密保存的 `backend/.env`。

## 18. 常见故障

### 502 Bad Gateway

```bash
sudo systemctl status content-publish --no-pager
sudo journalctl -u content-publish -n 100 --no-pager
curl -v http://127.0.0.1:8000/api/health
```

### 数据库连接失败

```bash
sudo systemctl status postgresql --no-pager
sudo -u postgres pg_isready
grep '^DATABASE_URL=' /opt/content-publish/backend/.env
```

不要把含密码的完整 `DATABASE_URL` 粘贴到工单或聊天中。

### 上传返回 413

同时检查 Nginx `client_max_body_size` 和后端 `MAX_UPLOAD_SIZE_MB`；Nginx 应略大。修改后执行 `nginx -t` 和 `systemctl reload nginx`。

### Local 发布成功但 URL 404

检查 `publish_root` 是否对应 Nginx `/published/` 的 `alias`：

```bash
namei -l /srv/content-publish/published/html
sudo restorecon -RF /srv/content-publish/published
```

### GitHub Pages 发布失败

- Branch 必须等于 GitHub Settings → Pages 中的实际发布分支。
- `repo_path` 必须位于 Pages 发布源内。
- Token 需要仓库内容读写权限。
- `credential_ref=publish_test` 对应 `PUBLISH_CREDENTIAL_PUBLISH_TEST_TOKEN`。
- 修改 `.env` 后重启服务。
- GitHub Pages 官方不支持 Git LFS。单个文件超过 100 MiB 时请改用 GitHub Repository、公司服务器、SFTP、OneDrive 或 Dropbox；普通 GitHub Repository 目标会自动使用 Git LFS。
- Pages 构建最长可能持续数分钟；前端会进入详情页自动刷新状态，不要因浏览器短超时重复点击发布。

Nginx 日志：

```bash
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```

## 19. 官方参考

- [PostgreSQL：Red Hat 家族安装](https://www.postgresql.org/download/linux/redhat/)
- [RHEL 9：配置 PostgreSQL](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_using_database_servers/using-postgresql_configuring-and-using-database-servers)
- [RHEL 9：安装 Python](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/installing_and_using_dynamic_programming_languages/assembly_installing-and-using-python-3_installing-and-using-dynamic-programming-languages)
- [Python：venv](https://docs.python.org/3.11/tutorial/venv.html)
- [RHEL 9：配置 Nginx](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/deploying_web_servers_and_reverse_proxies/setting-up-and-configuring-nginx_deploying-web-servers-and-reverse-proxies)
