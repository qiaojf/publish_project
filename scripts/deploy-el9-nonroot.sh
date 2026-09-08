#!/usr/bin/env bash
set -Eeuo pipefail

ACTION="${1:-install}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

die() { echo "[ERROR] $*" >&2; exit 1; }
notice() { echo "[INFO] $*"; }

if (( EUID == 0 )); then
  die "这是非 root 部署脚本，请使用普通登录用户运行，不要使用 sudo。"
fi

if [[ -f "$SCRIPT_DIR/../config/runtime.env" ]]; then
  DEFAULT_INSTALL_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
  DEFAULT_SOURCE_ROOT="$DEFAULT_INSTALL_ROOT/app"
else
  DEFAULT_INSTALL_ROOT="$HOME/.local/share/content-publish"
  DEFAULT_SOURCE_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
fi

INSTALL_ROOT="${INSTALL_ROOT:-$DEFAULT_INSTALL_ROOT}"
HOME_REAL="$(readlink -f -- "$HOME")"
INSTALL_REAL="$(readlink -m -- "$INSTALL_ROOT")"
[[ $INSTALL_REAL != "$HOME_REAL" && $INSTALL_REAL == "$HOME_REAL/"* ]] || die "INSTALL_ROOT 必须是当前用户 HOME 下的独立子目录。"
[[ $INSTALL_REAL != *[[:space:]]* && $INSTALL_REAL != *"'"* && $INSTALL_REAL != *'"'* ]] || die "INSTALL_ROOT 不能包含空白或引号。"
INSTALL_ROOT="$INSTALL_REAL"
CONFIG_ROOT="$INSTALL_ROOT/config"
RUNTIME_ENV="$CONFIG_ROOT/runtime.env"

is_positive_port() {
  [[ $1 =~ ^[0-9]+$ ]] && (( 10#$1 >= 1024 && 10#$1 <= 65535 ))
}

healthcheck() {
  "$PYTHON" - "http://127.0.0.1:${WEB_PORT}/api/health" <<'PY'
import json
import sys
from urllib.request import urlopen

with urlopen(sys.argv[1], timeout=5) as response:
    body = json.load(response)
if response.status != 200 or not body.get("success") or body.get("data", {}).get("status") != "ok":
    raise SystemExit(1)
PY
}

load_runtime() {
  [[ -r $RUNTIME_ENV ]] || die "未找到部署配置：$RUNTIME_ENV；请先执行 install。"
  # shellcheck disable=SC1090
  source "$RUNTIME_ENV"
  PYTHON="$RUNTIME_ROOT/bin/python"
  SUPERVISORD="$RUNTIME_ROOT/bin/supervisord"
  SUPERVISORCTL="$RUNTIME_ROOT/bin/supervisorctl"
  export PATH="$RUNTIME_ROOT/bin:${PATH:-/usr/local/bin:/usr/bin:/bin}"
  [[ -x $PYTHON && -x $SUPERVISORD && -x $SUPERVISORCTL ]] || die "运行环境不完整，请重新执行 install。"
}

stack_is_running() {
  [[ -s $RUN_ROOT/supervisord.pid ]] || return 1
  local pid
  pid="$(<"$RUN_ROOT/supervisord.pid")"
  [[ $pid =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null
}

start_stack() {
  if stack_is_running; then
    notice "服务已经在运行。"
    "$SUPERVISORCTL" -c "$SUPERVISOR_CONFIG" status
    return
  fi
  rm -f -- "$RUN_ROOT/supervisor.sock" "$RUN_ROOT/supervisord.pid"
  "$SUPERVISORD" -c "$SUPERVISOR_CONFIG"
  for _ in {1..60}; do
    if healthcheck >/dev/null 2>&1; then
      "$SUPERVISORCTL" -c "$SUPERVISOR_CONFIG" status
      notice "健康检查通过：http://127.0.0.1:${WEB_PORT}/api/health"
      return
    fi
    sleep 1
  done
  "$SUPERVISORCTL" -c "$SUPERVISOR_CONFIG" status || true
  die "服务未在 60 秒内通过健康检查，请查看 $LOG_ROOT。"
}

stop_stack() {
  if ! stack_is_running; then
    notice "服务当前未运行。"
    rm -f -- "$RUN_ROOT/supervisor.sock" "$RUN_ROOT/supervisord.pid"
    return
  fi
  "$SUPERVISORCTL" -c "$SUPERVISOR_CONFIG" shutdown
  for _ in {1..30}; do
    stack_is_running || { notice "服务已停止。"; return; }
    sleep 1
  done
  die "Supervisor 未能正常停止，请检查 $LOG_ROOT/supervisord.log。"
}

show_status() {
  if ! stack_is_running; then
    echo "content-publish: stopped"
    return 1
  fi
  "$SUPERVISORCTL" -c "$SUPERVISOR_CONFIG" status
  if healthcheck >/dev/null 2>&1; then
    echo "health: ok"
  else
    echo "health: failed"
    return 1
  fi
}

user_service_action() {
  command -v systemctl >/dev/null 2>&1 || die "系统没有 systemctl，无法管理用户服务。"
  case "$1" in
    start|restart)
      systemctl --user "$1" content-publish.service
      for _ in {1..60}; do
        if healthcheck >/dev/null 2>&1; then
          systemctl --user --no-pager status content-publish.service || true
          echo "health: ok"
          return
        fi
        sleep 1
      done
      systemctl --user --no-pager status content-publish.service || true
      die "用户服务未在 60 秒内通过健康检查，请查看 $LOG_ROOT。"
      ;;
    stop)
      systemctl --user stop content-publish.service
      ;;
    status)
      systemctl --user --no-pager status content-publish.service
      healthcheck >/dev/null 2>&1 || die "用户服务正在运行，但健康检查失败。"
      echo "health: ok"
      ;;
  esac
}

case "$ACTION" in
  start)
    load_runtime
    if [[ ${ENABLE_USER_SYSTEMD:-0} == 1 ]]; then user_service_action start; else start_stack; fi
    exit 0
    ;;
  stop)
    load_runtime
    if [[ ${ENABLE_USER_SYSTEMD:-0} == 1 ]]; then user_service_action stop; else stop_stack; fi
    exit 0
    ;;
  restart)
    load_runtime
    if [[ ${ENABLE_USER_SYSTEMD:-0} == 1 ]]; then
      user_service_action restart
    else
      stop_stack
      start_stack
    fi
    exit 0
    ;;
  status)
    load_runtime
    if [[ ${ENABLE_USER_SYSTEMD:-0} == 1 ]]; then user_service_action status; else show_status; fi
    exit $?
    ;;
  install) ;;
  *) die "用法：$0 [install|start|stop|restart|status]" ;;
esac

SOURCE_ROOT="${SOURCE_ROOT:-$DEFAULT_SOURCE_ROOT}"
APP_ROOT="$INSTALL_ROOT/app"
DATA_ROOT="$INSTALL_ROOT/data"
RUNTIME_ROOT="$INSTALL_ROOT/runtime"
TOOLS_ROOT="$INSTALL_ROOT/tools"
RUN_ROOT="$INSTALL_ROOT/run"
LOG_ROOT="$INSTALL_ROOT/logs"
PGDATA="$INSTALL_ROOT/postgres/data"
PG_SOCKET_DIR="$INSTALL_ROOT/postgres/socket"
BACKEND_ROOT="$APP_ROOT/backend"
BACKEND_ENV="$BACKEND_ROOT/.env"
SUPERVISOR_CONFIG="$CONFIG_ROOT/supervisord.conf"
CADDY_CONFIG="$CONFIG_ROOT/Caddyfile"
CONTROL_BIN="$INSTALL_ROOT/bin/content-publishctl"

REQUESTED_PUBLIC_URL="${PUBLIC_URL:-}"
REQUESTED_DATA_ROOT="${PUBLISH_DATA_ROOT:-}"
REQUESTED_WEB_PORT="${WEB_PORT:-}"
REQUESTED_API_PORT="${API_PORT:-}"
REQUESTED_DB_PORT="${DB_PORT:-}"
REQUESTED_RUN_TESTS="${RUN_TESTS:-}"
REQUESTED_MAX_UPLOAD="${MAX_UPLOAD_SIZE_MB:-}"
REQUESTED_WORKERS="${UVICORN_WORKERS:-}"
REQUESTED_MANAGED_DB="${MANAGED_POSTGRES:-}"
REQUESTED_ENABLE_SYSTEMD="${ENABLE_USER_SYSTEMD:-}"
PREVIOUS_PUBLIC_URL=""
PREVIOUS_DATA_ROOT=""
PREVIOUS_DB_PORT=""
PREVIOUS_MAX_UPLOAD=""
PREVIOUS_MANAGED_DB=""
PREVIOUS_ENABLE_SYSTEMD="0"
if [[ -r $RUNTIME_ENV ]]; then
  # Preserve prior deployment ports and mode unless this run explicitly overrides them.
  # shellcheck disable=SC1090
  source "$RUNTIME_ENV"
  PREVIOUS_PUBLIC_URL="${PUBLIC_URL:-}"
  PREVIOUS_DATA_ROOT="${DATA_ROOT:-}"
  PREVIOUS_DB_PORT="${DB_PORT:-}"
  PREVIOUS_MAX_UPLOAD="${MAX_UPLOAD_SIZE_MB:-}"
  PREVIOUS_MANAGED_DB="${MANAGED_POSTGRES:-}"
  PREVIOUS_ENABLE_SYSTEMD="${ENABLE_USER_SYSTEMD:-0}"
fi

WEB_PORT="${REQUESTED_WEB_PORT:-${WEB_PORT:-18080}}"
API_PORT="${REQUESTED_API_PORT:-${API_PORT:-18000}}"
DB_PORT="${REQUESTED_DB_PORT:-${DB_PORT:-15432}}"
RUN_TESTS="${REQUESTED_RUN_TESTS:-${RUN_TESTS:-0}}"
MAX_UPLOAD_SIZE_MB="${REQUESTED_MAX_UPLOAD:-${MAX_UPLOAD_SIZE_MB:-1024}}"
UVICORN_WORKERS="${REQUESTED_WORKERS:-${UVICORN_WORKERS:-2}}"
DATA_ROOT="${REQUESTED_DATA_ROOT:-${DATA_ROOT:-$INSTALL_ROOT/data}}"
PUBLIC_URL="${REQUESTED_PUBLIC_URL:-${PUBLIC_URL:-http://$(hostname -f 2>/dev/null || hostname):$WEB_PORT}}"
PUBLIC_URL="${PUBLIC_URL%/}"
FORCE_CONFIG="${FORCE_CONFIG:-0}"
ENABLE_USER_SYSTEMD="${REQUESTED_ENABLE_SYSTEMD:-${ENABLE_USER_SYSTEMD:-0}}"
EXTERNAL_DATABASE_URL="${DATABASE_URL:-}"
EXTERNAL_TEST_DATABASE_URL="${TEST_DATABASE_URL:-}"

if [[ -n $EXTERNAL_DATABASE_URL ]]; then
  MANAGED_POSTGRES=0
elif [[ -n $REQUESTED_MANAGED_DB ]]; then
  MANAGED_POSTGRES="$REQUESTED_MANAGED_DB"
else
  MANAGED_POSTGRES="${MANAGED_POSTGRES:-1}"
fi

DATA_REAL="$(readlink -m -- "$DATA_ROOT")"
[[ $DATA_REAL != "$HOME_REAL" && $DATA_REAL == "$HOME_REAL/"* ]] || die "PUBLISH_DATA_ROOT 必须是当前用户 HOME 下的独立子目录。"
[[ $DATA_REAL != *[[:space:]]* && $DATA_REAL != *"'"* && $DATA_REAL != *'"'* ]] || die "PUBLISH_DATA_ROOT 不能包含空白或引号。"
DATA_ROOT="$DATA_REAL"

mkdir -p -- "$INSTALL_ROOT"
[[ -d $SOURCE_ROOT && -f $SOURCE_ROOT/package.json && -f $SOURCE_ROOT/backend/requirements.txt && -f $SOURCE_ROOT/scripts/deploy-el9-nonroot.sh ]] || die "SOURCE_ROOT 不是完整项目目录：$SOURCE_ROOT"

if [[ -r /etc/os-release ]]; then
  os_version="$(sed -n 's/^VERSION_ID=//p' /etc/os-release)"
  os_version="${os_version#\"}"
  os_version="${os_version%\"}"
  os_version="${os_version#\'}"
  os_version="${os_version%\'}"
  [[ ${os_version%%.*} == 9 ]] || die "该脚本仅面向 Enterprise Linux 9 兼容系统；检测到 VERSION_ID=${os_version:-unknown}。"
fi

for value in "$WEB_PORT" "$API_PORT" "$DB_PORT"; do
  is_positive_port "$value" || die "端口必须在 1024-65535 之间：$value"
done
[[ $WEB_PORT != "$API_PORT" && $WEB_PORT != "$DB_PORT" && $API_PORT != "$DB_PORT" ]] || die "WEB_PORT、API_PORT、DB_PORT 不能重复。"
[[ $RUN_TESTS =~ ^[01]$ && $FORCE_CONFIG =~ ^[01]$ && $ENABLE_USER_SYSTEMD =~ ^[01]$ && $MANAGED_POSTGRES =~ ^[01]$ ]] || die "布尔变量只能是 0 或 1。"
[[ $MAX_UPLOAD_SIZE_MB =~ ^[0-9]+$ && $UVICORN_WORKERS =~ ^[0-9]+$ ]] || die "MAX_UPLOAD_SIZE_MB 和 UVICORN_WORKERS 必须是正整数。"
(( 10#$MAX_UPLOAD_SIZE_MB >= 1 && 10#$MAX_UPLOAD_SIZE_MB <= 1024 )) || die "MAX_UPLOAD_SIZE_MB 必须在 1-1024 之间。"
(( 10#$UVICORN_WORKERS >= 1 )) || die "UVICORN_WORKERS 必须大于 0。"

if [[ -f $BACKEND_ENV && $FORCE_CONFIG == 0 ]]; then
  changed_settings=()
  [[ -z $REQUESTED_PUBLIC_URL || -z $PREVIOUS_PUBLIC_URL || $PUBLIC_URL == "${PREVIOUS_PUBLIC_URL%/}" ]] || changed_settings+=(PUBLIC_URL)
  if [[ -n $REQUESTED_DATA_ROOT && -n $PREVIOUS_DATA_ROOT ]]; then
    [[ $DATA_ROOT == "$(readlink -m -- "$PREVIOUS_DATA_ROOT")" ]] || changed_settings+=(PUBLISH_DATA_ROOT)
  fi
  [[ -z $REQUESTED_DB_PORT || -z $PREVIOUS_DB_PORT || $DB_PORT == "$PREVIOUS_DB_PORT" ]] || changed_settings+=(DB_PORT)
  [[ -z $REQUESTED_MAX_UPLOAD || -z $PREVIOUS_MAX_UPLOAD || $MAX_UPLOAD_SIZE_MB == "$PREVIOUS_MAX_UPLOAD" ]] || changed_settings+=(MAX_UPLOAD_SIZE_MB)
  [[ -z $REQUESTED_MANAGED_DB || -z $PREVIOUS_MANAGED_DB || $MANAGED_POSTGRES == "$PREVIOUS_MANAGED_DB" ]] || changed_settings+=(MANAGED_POSTGRES)
  if [[ -n $EXTERNAL_DATABASE_URL ]]; then
    EXISTING_DATABASE_URL="$(sed -n 's/^DATABASE_URL=//p' "$BACKEND_ENV")"
    [[ $EXTERNAL_DATABASE_URL == "$EXISTING_DATABASE_URL" ]] || changed_settings+=(DATABASE_URL)
  fi
  if [[ -n $EXTERNAL_TEST_DATABASE_URL ]]; then
    EXISTING_TEST_DATABASE_URL="$(sed -n 's/^TEST_DATABASE_URL=//p' "$BACKEND_ENV")"
    [[ $EXTERNAL_TEST_DATABASE_URL == "$EXISTING_TEST_DATABASE_URL" ]] || changed_settings+=(TEST_DATABASE_URL)
  fi
  if (( ${#changed_settings[@]} > 0 )); then
    die "以下参数会改变后端配置但现有 .env 正在受保护：${changed_settings[*]}。请先备份 .env，再显式设置 FORCE_CONFIG=1；脚本会沿用原 JWT_SECRET_KEY。"
  fi
fi

mkdir -p -- "$APP_ROOT" "$DATA_ROOT/source" "$DATA_ROOT/preview" "$DATA_ROOT/build" "$DATA_ROOT/published" \
  "$TOOLS_ROOT" "$RUN_ROOT" "$LOG_ROOT" "$PG_SOCKET_DIR" "$CONFIG_ROOT" "$INSTALL_ROOT/bin"
chmod 700 "$CONFIG_ROOT" "$RUN_ROOT" "$PG_SOCKET_DIR"

if [[ $PREVIOUS_ENABLE_SYSTEMD == 1 ]]; then
  command -v systemctl >/dev/null 2>&1 || die "旧部署使用用户 systemd，但当前找不到 systemctl。"
  systemctl --user stop content-publish.service
elif [[ -x $RUNTIME_ROOT/bin/supervisorctl && -r $SUPERVISOR_CONFIG ]]; then
  PYTHON="$RUNTIME_ROOT/bin/python"
  SUPERVISORD="$RUNTIME_ROOT/bin/supervisord"
  SUPERVISORCTL="$RUNTIME_ROOT/bin/supervisorctl"
  stop_stack
fi

cleanup_download=""
LOCAL_DB_STARTED=0
cleanup_on_exit() {
  local status=$?
  [[ -z $cleanup_download ]] || rm -f -- "$cleanup_download"
  if (( status != 0 && LOCAL_DB_STARTED == 1 )) && [[ -x $RUNTIME_ROOT/bin/pg_ctl ]]; then
    "$RUNTIME_ROOT/bin/pg_ctl" -D "$PGDATA" stop -m fast >/dev/null 2>&1 || true
  fi
  if (( status != 0 )); then
    echo "[ERROR] 部署失败，请查看上方错误和 $LOG_ROOT 中的日志。" >&2
  fi
}
trap cleanup_on_exit EXIT

echo "[1/10] 安装用户级 Python、Node.js、PostgreSQL、Caddy 运行环境..."
MICROMAMBA="$TOOLS_ROOT/micromamba"
if [[ ! -x $MICROMAMBA ]]; then
  command -v tar >/dev/null 2>&1 || die "系统缺少 tar，请联系管理员安装或预先上传 micromamba。"
  arch="$(uname -m)"
  case "$arch" in
    x86_64) mamba_arch="linux-64" ;;
    aarch64) mamba_arch="linux-aarch64" ;;
    *) die "暂不支持的 CPU 架构：$arch" ;;
  esac
  cleanup_download="$TOOLS_ROOT/micromamba.tar.bz2"
  download_url="${MICROMAMBA_DOWNLOAD_URL:-https://micro.mamba.pm/api/micromamba/${mamba_arch}/latest}"
  if command -v curl >/dev/null 2>&1; then
    curl -fL --retry 3 --connect-timeout 20 "$download_url" -o "$cleanup_download"
  elif command -v wget >/dev/null 2>&1; then
    wget --https-only --tries=3 --timeout=20 -O "$cleanup_download" "$download_url"
  else
    die "系统必须已有 curl 或 wget；两者都没有时请联系管理员或手动上传 micromamba。"
  fi
  tar -xjf "$cleanup_download" -C "$TOOLS_ROOT" --strip-components=1 bin/micromamba
  chmod 700 "$MICROMAMBA"
fi
export MAMBA_ROOT_PREFIX="$INSTALL_ROOT/.micromamba"
runtime_packages=("python=3.12" pip "nodejs=22" "postgresql=16" "caddy>=2.10,<3" rsync)
if [[ -x $RUNTIME_ROOT/bin/python ]]; then
  "$MICROMAMBA" install -y -p "$RUNTIME_ROOT" -c conda-forge "${runtime_packages[@]}"
else
  "$MICROMAMBA" create -y -p "$RUNTIME_ROOT" -c conda-forge "${runtime_packages[@]}"
fi
PYTHON="$RUNTIME_ROOT/bin/python"
NPM="$RUNTIME_ROOT/bin/npm"
RSYNC="$RUNTIME_ROOT/bin/rsync"
export PATH="$RUNTIME_ROOT/bin:${PATH:-/usr/local/bin:/usr/bin:/bin}"
hash -r
[[ $(command -v node) == "$RUNTIME_ROOT/bin/node" ]] || die "用户级 Node.js 未进入 PATH：$RUNTIME_ROOT/bin/node"
"$RUNTIME_ROOT/bin/node" --version
"$NPM" --version

"$PYTHON" - "$PUBLIC_URL" <<'PY'
import sys
from urllib.parse import urlsplit

value = sys.argv[1]
parsed = urlsplit(value)
if (
    any(char.isspace() for char in value)
    or parsed.scheme not in {"http", "https"}
    or not parsed.hostname
    or parsed.username is not None
    or parsed.password is not None
    or parsed.path not in {"", "/"}
    or parsed.query
    or parsed.fragment
):
    raise SystemExit("PUBLIC_URL 必须是无路径、无账号信息的完整 http(s) 地址，例如 https://publish.example.com")
try:
    parsed.port
except ValueError as exc:
    raise SystemExit(f"PUBLIC_URL 端口无效：{exc}") from exc
PY

echo "[2/10] 同步项目代码..."
if [[ "$(readlink -f -- "$SOURCE_ROOT")" != "$(readlink -f -- "$APP_ROOT")" ]]; then
  "$RSYNC" -a --delete \
    --exclude='.git/' --exclude='node_modules/' --exclude='dist/' --exclude='local-data/' \
    --exclude='.env' --exclude='.env.local' --exclude='.env.production' \
    --exclude='backend/.env' --exclude='backend/.venv/' --exclude='__pycache__/' \
    --exclude='.ssh/' --exclude='id_rsa*' --exclude='id_ed25519*' \
    --exclude='*.pem' --exclude='*.key' --exclude='*.p12' --exclude='*.pfx' \
    "$SOURCE_ROOT/" "$APP_ROOT/"
fi

echo "[3/10] 安装后端与进程管理依赖..."
"$PYTHON" -m pip install --upgrade pip setuptools wheel
"$PYTHON" -m pip install -r "$BACKEND_ROOT/requirements.txt"
"$PYTHON" -m pip install "supervisor>=4.2,<5"
"$PYTHON" -m pip check

random_hex() { "$PYTHON" -c "import secrets; print(secrets.token_hex(int('$1')))"; }
DB_PASSWORD_FILE="$CONFIG_ROOT/postgres-password"
INITIAL_CREDENTIALS_FILE="$CONFIG_ROOT/initial-credentials.txt"
if [[ $MANAGED_POSTGRES == 1 && ! -s $DB_PASSWORD_FILE ]]; then
  random_hex 24 > "$DB_PASSWORD_FILE"
  chmod 600 "$DB_PASSWORD_FILE"
fi
if [[ ! -s $INITIAL_CREDENTIALS_FILE ]]; then
  {
    echo "admin=$(random_hex 12)"
    echo "employee=$(random_hex 12)"
  } > "$INITIAL_CREDENTIALS_FILE"
  chmod 600 "$INITIAL_CREDENTIALS_FILE"
fi
INITIAL_ADMIN_PASSWORD="$(sed -n 's/^admin=//p' "$INITIAL_CREDENTIALS_FILE")"
INITIAL_EMPLOYEE_PASSWORD="$(sed -n 's/^employee=//p' "$INITIAL_CREDENTIALS_FILE")"
[[ -n $INITIAL_ADMIN_PASSWORD && -n $INITIAL_EMPLOYEE_PASSWORD ]] || die "初始账号密码文件格式不正确：$INITIAL_CREDENTIALS_FILE"

echo "[4/10] 配置并启动 PostgreSQL..."
if [[ $MANAGED_POSTGRES == 1 ]]; then
  DB_USER="${DB_USER:-content_publish}"
  DB_NAME="${DB_NAME:-content_publish}"
  TEST_DB_NAME="${TEST_DB_NAME:-content_publish_test}"
  [[ $DB_USER =~ ^[A-Za-z_][A-Za-z0-9_]*$ && $DB_NAME =~ ^[A-Za-z_][A-Za-z0-9_]*$ && $TEST_DB_NAME =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "数据库名称和用户只能包含字母、数字、下划线，且不能以数字开头。"
  DB_PASSWORD="$(<"$DB_PASSWORD_FILE")"
  if [[ ! -s $PGDATA/PG_VERSION ]]; then
    mkdir -p -- "$PGDATA"
    chmod 700 "$PGDATA"
    "$RUNTIME_ROOT/bin/initdb" -D "$PGDATA" --username="$DB_USER" --pwfile="$DB_PASSWORD_FILE" \
      --auth-host=scram-sha-256 --auth-local=trust --encoding=UTF8 --locale=C
  fi
  cat > "$CONFIG_ROOT/postgresql.conf" <<EOF
listen_addresses = '127.0.0.1'
port = ${DB_PORT}
unix_socket_directories = '${PG_SOCKET_DIR}'
password_encryption = 'scram-sha-256'
max_connections = 100
shared_buffers = '128MB'
EOF
  if ! grep -Fq "include_if_exists = '${CONFIG_ROOT}/postgresql.conf'" "$PGDATA/postgresql.conf"; then
    echo "include_if_exists = '${CONFIG_ROOT}/postgresql.conf'" >> "$PGDATA/postgresql.conf"
  fi
  if ! "$RUNTIME_ROOT/bin/pg_ctl" -D "$PGDATA" status >/dev/null 2>&1; then
    "$RUNTIME_ROOT/bin/pg_ctl" -D "$PGDATA" -l "$LOG_ROOT/postgresql-bootstrap.log" start -w -t 60
    LOCAL_DB_STARTED=1
  fi
  export PGPASSWORD="$DB_PASSWORD"
  db_exists="$($RUNTIME_ROOT/bin/psql -h 127.0.0.1 -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'")"
  [[ $db_exists == 1 ]] || "$RUNTIME_ROOT/bin/createdb" -h 127.0.0.1 -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
  if [[ $RUN_TESTS == 1 ]]; then
    test_db_exists="$($RUNTIME_ROOT/bin/psql -h 127.0.0.1 -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$TEST_DB_NAME'")"
    [[ $test_db_exists == 1 ]] || "$RUNTIME_ROOT/bin/createdb" -h 127.0.0.1 -p "$DB_PORT" -U "$DB_USER" "$TEST_DB_NAME"
  fi
  ENCODED_DB_PASSWORD="$($PYTHON - "$DB_PASSWORD" <<'PY'
import sys
from urllib.parse import quote
print(quote(sys.argv[1], safe=""))
PY
)"
  ACTIVE_DATABASE_URL="postgresql+psycopg://${DB_USER}:${ENCODED_DB_PASSWORD}@127.0.0.1:${DB_PORT}/${DB_NAME}"
  ACTIVE_TEST_DATABASE_URL="postgresql+psycopg://${DB_USER}:${ENCODED_DB_PASSWORD}@127.0.0.1:${DB_PORT}/${TEST_DB_NAME}"
else
  if [[ ! -f $BACKEND_ENV || $FORCE_CONFIG == 1 ]]; then
    [[ $EXTERNAL_DATABASE_URL == postgresql+psycopg://* ]] || die "使用外部数据库时必须传入 DATABASE_URL=postgresql+psycopg://..."
    if [[ $RUN_TESTS == 1 ]]; then
      [[ $EXTERNAL_TEST_DATABASE_URL == postgresql+psycopg://* && $EXTERNAL_TEST_DATABASE_URL != "$EXTERNAL_DATABASE_URL" ]] || die "RUN_TESTS=1 时必须传入独立的 TEST_DATABASE_URL。"
    fi
    ACTIVE_DATABASE_URL="$EXTERNAL_DATABASE_URL"
    ACTIVE_TEST_DATABASE_URL="${EXTERNAL_TEST_DATABASE_URL:-$EXTERNAL_DATABASE_URL}"
  fi
fi

echo "[5/10] 生成后端配置..."
if [[ ! -f $BACKEND_ENV || $FORCE_CONFIG == 1 ]]; then
  EXISTING_JWT_SECRET=""
  if [[ -r $BACKEND_ENV ]]; then
    EXISTING_JWT_SECRET="$(sed -n 's/^JWT_SECRET_KEY=//p' "$BACKEND_ENV")"
  fi
  JWT_SECRET_KEY="${JWT_SECRET_KEY:-${EXISTING_JWT_SECRET:-$(random_hex 48)}}"
  if [[ $MANAGED_POSTGRES == 0 ]]; then
    "$PYTHON" - "$ACTIVE_DATABASE_URL" "$ACTIVE_TEST_DATABASE_URL" <<'PY'
import sys
from urllib.parse import urlsplit

for name, value in zip(("DATABASE_URL", "TEST_DATABASE_URL"), sys.argv[1:]):
    parsed = urlsplit(value)
    if any(char.isspace() for char in value) or parsed.scheme != "postgresql+psycopg" or not parsed.hostname or not parsed.path.strip("/"):
        raise SystemExit(f"{name} 格式无效；请使用 postgresql+psycopg://user:encoded-password@host:port/database")
    try:
        parsed.port
    except ValueError as exc:
        raise SystemExit(f"{name} 端口无效：{exc}") from exc
PY
  fi
  cat > "$BACKEND_ENV" <<EOF
APP_NAME=Internal Content Publish Platform
APP_ENV=production
DEBUG=false
DATABASE_URL=${ACTIVE_DATABASE_URL}
TEST_DATABASE_URL=${ACTIVE_TEST_DATABASE_URL}
JWT_SECRET_KEY=${JWT_SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=480
SOURCE_STORAGE_ROOT=${DATA_ROOT}/source
PREVIEW_STORAGE_ROOT=${DATA_ROOT}/preview
BUILD_STORAGE_ROOT=${DATA_ROOT}/build
LOCAL_PUBLISHED_ROOT=${DATA_ROOT}/published
LOCAL_PUBLISHED_BASE_URL=${PUBLIC_URL}/published
MAX_UPLOAD_SIZE_MB=${MAX_UPLOAD_SIZE_MB}
PUBLISH_CONNECTION_TIMEOUT_SECONDS=30
PUBLISH_OPERATION_TIMEOUT_SECONDS=600
CORS_ORIGINS=${PUBLIC_URL}
DB_CONNECT_TIMEOUT_SECONDS=5
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
EOF
  chmod 600 "$BACKEND_ENV"
else
  notice "保留现有 $BACKEND_ENV；如需重建，显式设置 FORCE_CONFIG=1。"
fi

echo "[6/10] 执行数据库迁移和初始化数据..."
(
  cd "$BACKEND_ROOT"
  "$PYTHON" -m alembic upgrade head
  "$PYTHON" - <<'PY'
from sqlalchemy import text

from app.db.session import engine

with engine.connect() as connection:
    connection.execute(text(
        "SELECT id, name, enabled, sort_order, visibility_scope, department, created_at, updated_at "
        "FROM categories LIMIT 1"
    ))
    connection.execute(text("SELECT department FROM users LIMIT 1"))
    connection.execute(text("SELECT id, name, enabled, sort_order FROM departments LIMIT 1"))
print("Database schema check passed: departments, users.department and category visibility")
PY
  SEED_ADMIN_PASSWORD="$INITIAL_ADMIN_PASSWORD" SEED_EMPLOYEE_PASSWORD="$INITIAL_EMPLOYEE_PASSWORD" "$PYTHON" scripts/seed.py
)

if [[ $RUN_TESTS == 1 ]]; then
  (
    cd "$BACKEND_ROOT"
    "$PYTHON" -m pytest -q
  )
else
  notice "跳过 pytest；需要执行时设置 RUN_TESTS=1。"
fi

echo "[7/10] 安装前端依赖并构建..."
(
  cd "$APP_ROOT"
  VITE_API_BASE_URL=/api VITE_USE_MOCK=false "$NPM" ci
  VITE_API_BASE_URL=/api VITE_USE_MOCK=false "$NPM" run build
)

echo "[8/10] 生成 Caddy 与 Supervisor 配置..."
cat > "$CADDY_CONFIG" <<EOF
{
    admin off
    auto_https off
}

:${WEB_PORT} {
    encode zstd gzip

    handle /api/* {
        reverse_proxy 127.0.0.1:${API_PORT} {
            transport http {
                dial_timeout 30s
                response_header_timeout 720s
            }
        }
    }

    handle_path /published/* {
        root * ${DATA_ROOT}/published
        file_server
    }

    handle {
        root * ${APP_ROOT}/dist
        try_files {path} /index.html
        file_server
    }

    log {
        output file ${LOG_ROOT}/caddy-access.log {
            roll_size 20MiB
            roll_keep 5
        }
    }
}
EOF
"$RUNTIME_ROOT/bin/caddy" validate --config "$CADDY_CONFIG" --adapter caddyfile

cat > "$SUPERVISOR_CONFIG" <<EOF
[unix_http_server]
file=${RUN_ROOT}/supervisor.sock
chmod=0700

[supervisord]
logfile=${LOG_ROOT}/supervisord.log
pidfile=${RUN_ROOT}/supervisord.pid
childlogdir=${LOG_ROOT}
nodaemon=false
minfds=1024
environment=PATH="${RUNTIME_ROOT}/bin:/usr/local/bin:/usr/bin:/bin"

[rpcinterface:supervisor]
supervisor.rpcinterface_factory=supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix://${RUN_ROOT}/supervisor.sock

EOF
if [[ $MANAGED_POSTGRES == 1 ]]; then
  cat >> "$SUPERVISOR_CONFIG" <<EOF
[program:postgresql]
command=${RUNTIME_ROOT}/bin/postgres -D ${PGDATA}
priority=10
autostart=true
autorestart=true
startsecs=3
stopsignal=INT
stopwaitsecs=60
redirect_stderr=true
stdout_logfile=${LOG_ROOT}/postgresql.log
stdout_logfile_maxbytes=20MB
stdout_logfile_backups=5

EOF
fi
cat >> "$SUPERVISOR_CONFIG" <<EOF
[program:backend]
command=${PYTHON} -m uvicorn app.main:app --host 127.0.0.1 --port ${API_PORT} --workers ${UVICORN_WORKERS} --proxy-headers --forwarded-allow-ips=127.0.0.1
directory=${BACKEND_ROOT}
priority=20
autostart=true
autorestart=true
startsecs=3
stopasgroup=true
killasgroup=true
redirect_stderr=true
stdout_logfile=${LOG_ROOT}/backend.log
stdout_logfile_maxbytes=20MB
stdout_logfile_backups=5

[program:caddy]
command=${RUNTIME_ROOT}/bin/caddy run --config ${CADDY_CONFIG} --adapter caddyfile
directory=${INSTALL_ROOT}
priority=30
autostart=true
autorestart=true
startsecs=3
stopasgroup=true
killasgroup=true
redirect_stderr=true
stdout_logfile=${LOG_ROOT}/caddy.log
stdout_logfile_maxbytes=20MB
stdout_logfile_backups=5
EOF
chmod 600 "$SUPERVISOR_CONFIG" "$CADDY_CONFIG"

{
  printf 'INSTALL_ROOT=%q\n' "$INSTALL_ROOT"
  printf 'APP_ROOT=%q\n' "$APP_ROOT"
  printf 'DATA_ROOT=%q\n' "$DATA_ROOT"
  printf 'RUNTIME_ROOT=%q\n' "$RUNTIME_ROOT"
  printf 'RUN_ROOT=%q\n' "$RUN_ROOT"
  printf 'LOG_ROOT=%q\n' "$LOG_ROOT"
  printf 'PGDATA=%q\n' "$PGDATA"
  printf 'WEB_PORT=%q\n' "$WEB_PORT"
  printf 'API_PORT=%q\n' "$API_PORT"
  printf 'DB_PORT=%q\n' "$DB_PORT"
  printf 'PUBLIC_URL=%q\n' "$PUBLIC_URL"
  printf 'MAX_UPLOAD_SIZE_MB=%q\n' "$MAX_UPLOAD_SIZE_MB"
  printf 'UVICORN_WORKERS=%q\n' "$UVICORN_WORKERS"
  printf 'RUN_TESTS=%q\n' "$RUN_TESTS"
  printf 'MANAGED_POSTGRES=%q\n' "$MANAGED_POSTGRES"
  printf 'ENABLE_USER_SYSTEMD=%q\n' "$ENABLE_USER_SYSTEMD"
  printf 'SUPERVISOR_CONFIG=%q\n' "$SUPERVISOR_CONFIG"
} > "$RUNTIME_ENV"
chmod 600 "$RUNTIME_ENV"

cp -- "$SOURCE_ROOT/scripts/deploy-el9-nonroot.sh" "$CONTROL_BIN"
chmod 700 "$CONTROL_BIN"

USER_UNIT="$CONFIG_ROOT/content-publish.user.service"
cat > "$USER_UNIT" <<EOF
[Unit]
Description=Internal Content Publish Platform (user service)
After=network-online.target

[Service]
Type=forking
PIDFile=${RUN_ROOT}/supervisord.pid
ExecStart=${RUNTIME_ROOT}/bin/supervisord -c ${SUPERVISOR_CONFIG}
ExecStop=${RUNTIME_ROOT}/bin/supervisorctl -c ${SUPERVISOR_CONFIG} shutdown
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

if [[ $MANAGED_POSTGRES == 1 ]] && "$RUNTIME_ROOT/bin/pg_ctl" -D "$PGDATA" status >/dev/null 2>&1; then
  "$RUNTIME_ROOT/bin/pg_ctl" -D "$PGDATA" stop -m fast -w -t 60
  LOCAL_DB_STARTED=0
fi

echo "[9/10] 启动应用..."
if [[ $ENABLE_USER_SYSTEMD == 1 ]]; then
  command -v systemctl >/dev/null 2>&1 || die "系统没有 systemctl，不能启用用户服务。"
  mkdir -p -- "$HOME/.config/systemd/user"
  cp -- "$USER_UNIT" "$HOME/.config/systemd/user/content-publish.service"
  systemctl --user daemon-reload
  systemctl --user enable --now content-publish.service
  for _ in {1..60}; do
    if healthcheck >/dev/null 2>&1; then
      systemctl --user --no-pager status content-publish.service || true
      notice "健康检查通过：http://127.0.0.1:${WEB_PORT}/api/health"
      break
    fi
    sleep 1
  done
  if ! healthcheck >/dev/null 2>&1; then
    systemctl --user --no-pager status content-publish.service || true
    die "用户服务未在 60 秒内通过健康检查，请查看 $LOG_ROOT。"
  fi
else
  if [[ $PREVIOUS_ENABLE_SYSTEMD == 1 ]]; then
    systemctl --user disable content-publish.service
  fi
  SUPERVISORD="$RUNTIME_ROOT/bin/supervisord"
  SUPERVISORCTL="$RUNTIME_ROOT/bin/supervisorctl"
  start_stack
fi

echo "[10/10] 部署完成"
echo "访问地址：       ${PUBLIC_URL}/"
echo "服务器本机地址： http://127.0.0.1:${WEB_PORT}/"
echo "健康检查：       http://127.0.0.1:${WEB_PORT}/api/health"
echo "安装目录：       ${INSTALL_ROOT}"
echo "数据目录：       ${DATA_ROOT}"
echo "控制命令：       ${CONTROL_BIN} status|start|stop|restart"
echo "日志目录：       ${LOG_ROOT}"
echo "初始账号文件：   ${INITIAL_CREDENTIALS_FILE}（权限为 600；修改登录密码后其中记录不再代表当前密码）"
if [[ $ENABLE_USER_SYSTEMD != 1 ]]; then
  echo "重启自启动：     请按非 root 部署 README 配置用户 systemd、crontab 或主机控制面板。"
fi
echo "注意：普通用户不能开放防火墙或绑定 80/443；外网不可访问时需让管理员/主机面板转发到 ${WEB_PORT}。"
