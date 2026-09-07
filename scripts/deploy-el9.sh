#!/usr/bin/env bash
set -Eeuo pipefail

trap 'echo "[ERROR] Deployment failed at line ${LINENO}." >&2' ERR

if [[ ${EUID} -ne 0 ]]; then
  echo "Run this script as root: sudo bash scripts/deploy-el9.sh" >&2
  exit 1
fi

if ! command -v dnf >/dev/null 2>&1; then
  echo "This installer supports Enterprise Linux 9 systems with dnf." >&2
  exit 1
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
fi
OS_VERSION_ID="${VERSION_ID:-}"
if [[ ${OS_VERSION_ID%%.*} != "9" ]]; then
  echo "Detected VERSION_ID=${OS_VERSION_ID:-unknown}; this script is intended for Enterprise Linux 9." >&2
  exit 1
fi

SOURCE_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ROOT="${APP_ROOT:-/opt/content-publish}"
DATA_ROOT="${DATA_ROOT:-/srv/content-publish}"
WEB_ROOT="${WEB_ROOT:-/usr/share/nginx/html/content-publish}"
APP_USER="${APP_USER:-contentpub}"
APP_GROUP="${APP_GROUP:-contentpub}"
DB_NAME="${DB_NAME:-content_publish}"
TEST_DB_NAME="${TEST_DB_NAME:-content_publish_test}"
DB_USER="${DB_USER:-content_publish}"
RUN_TESTS="${RUN_TESTS:-0}"
FORCE_CONFIG="${FORCE_CONFIG:-0}"
MAX_UPLOAD_SIZE_MB="${MAX_UPLOAD_SIZE_MB:-1024}"
UVICORN_WORKERS="${UVICORN_WORKERS:-2}"
DEFAULT_HOST="$(hostname -f 2>/dev/null || hostname)"
PUBLIC_URL="${PUBLIC_URL:-http://${DEFAULT_HOST}}"
PUBLIC_URL="${PUBLIC_URL%/}"

for deploy_path in "$APP_ROOT" "$DATA_ROOT" "$WEB_ROOT"; do
  if [[ $deploy_path != /* || $deploy_path == "/" ]]; then
    echo "Deployment paths must be absolute and cannot be /: ${deploy_path}" >&2
    exit 1
  fi
done
case "$WEB_ROOT" in
  /usr/share/nginx/html/* | /var/www/* | /srv/* | /data/*) ;;
  *)
    echo "WEB_ROOT must be a dedicated subdirectory under /usr/share/nginx/html, /var/www, /srv or /data." >&2
    exit 1
    ;;
esac
if [[ $APP_ROOT == "$DATA_ROOT" || $APP_ROOT == "$WEB_ROOT" || $DATA_ROOT == "$WEB_ROOT" ]]; then
  echo "APP_ROOT, DATA_ROOT and WEB_ROOT must be different directories." >&2
  exit 1
fi
if [[ ! $APP_USER =~ ^[a-z_][a-z0-9_-]*$ || ! $APP_GROUP =~ ^[a-z_][a-z0-9_-]*$ ]]; then
  echo "APP_USER and APP_GROUP contain unsupported characters." >&2
  exit 1
fi
if [[ ! $DB_NAME =~ ^[A-Za-z_][A-Za-z0-9_]*$ || ! $TEST_DB_NAME =~ ^[A-Za-z_][A-Za-z0-9_]*$ || ! $DB_USER =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
  echo "DB_NAME, TEST_DB_NAME and DB_USER may contain only letters, digits and underscores." >&2
  exit 1
fi
if [[ ! $MAX_UPLOAD_SIZE_MB =~ ^[0-9]+$ || ! $UVICORN_WORKERS =~ ^[0-9]+$ ]]; then
  echo "MAX_UPLOAD_SIZE_MB and UVICORN_WORKERS must be positive integers." >&2
  exit 1
fi

echo "[1/12] Installing Enterprise Linux packages..."
dnf install -y curl git rsync openssl gcc gcc-c++ make libffi-devel openssl-devel \
  policycoreutils-python-utils python3.11 python3.11-pip python3.11-devel nginx

node_is_supported() {
  command -v node >/dev/null 2>&1 &&
    node -e 'const [major,minor]=process.versions.node.split(".").map(Number); process.exit((major>=22 || (major===20 && minor>=19)) ? 0 : 1)'
}

if ! node_is_supported; then
  dnf module reset -y nodejs || true
  dnf module enable -y nodejs:22 || true
  dnf install -y nodejs
fi
if ! node_is_supported; then
  echo "Node.js $(node --version 2>/dev/null || echo unavailable) is too old. Install Node.js 22, then rerun this script." >&2
  exit 1
fi

if ! rpm -q postgresql-server >/dev/null 2>&1; then
  dnf module reset -y postgresql || true
  dnf module enable -y postgresql:16 || true
  dnf install -y postgresql-server postgresql-contrib
fi

echo "[2/12] Initializing PostgreSQL..."
if [[ ! -s /var/lib/pgsql/data/PG_VERSION ]]; then
  postgresql-setup --initdb
fi
systemctl enable --now postgresql.service
for _ in {1..30}; do
  if pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if ! pg_isready -h 127.0.0.1 -p 5432 >/dev/null 2>&1; then
  echo "PostgreSQL did not become ready. Run: journalctl -u postgresql -n 100" >&2
  exit 1
fi

echo "[3/12] Creating service account and application directories..."
getent group "$APP_GROUP" >/dev/null 2>&1 || groupadd --system "$APP_GROUP"
if ! id "$APP_USER" >/dev/null 2>&1; then
  useradd --system --gid "$APP_GROUP" --home-dir "$APP_ROOT" --shell /sbin/nologin "$APP_USER"
fi
install -d -m 0750 -o "$APP_USER" -g "$APP_GROUP" "$APP_ROOT"
install -d -m 2770 -o "$APP_USER" -g "$APP_GROUP" \
  "$DATA_ROOT/source" "$DATA_ROOT/preview" "$DATA_ROOT/build" "$DATA_ROOT/published"
if id nginx >/dev/null 2>&1; then
  usermod -a -G "$APP_GROUP" nginx
fi

if [[ "$(readlink -f "$SOURCE_ROOT")" != "$(readlink -f "$APP_ROOT")" ]]; then
  rsync -a \
    --exclude='.git/' \
    --exclude='node_modules/' \
    --exclude='dist/' \
    --exclude='local-data/' \
    --exclude='.env' \
    --exclude='.env.local' \
    --exclude='.env.production' \
    --exclude='backend/.env' \
    --exclude='backend/.venv/' \
    --exclude='.ssh/' \
    --exclude='id_rsa*' \
    --exclude='id_ed25519*' \
    --exclude='*.pem' \
    --exclude='*.key' \
    --exclude='*.p12' \
    --exclude='*.pfx' \
    "$SOURCE_ROOT/" "$APP_ROOT/"
fi
chown -R "$APP_USER:$APP_GROUP" "$APP_ROOT"

BACKEND_ROOT="$APP_ROOT/backend"
BACKEND_ENV="$BACKEND_ROOT/.env"
VENV_ROOT="$BACKEND_ROOT/.venv"

PUBLIC_HOST="$(python3.11 - "$PUBLIC_URL" <<'PY'
import sys
from urllib.parse import urlsplit

url = urlsplit(sys.argv[1])
if (
    url.scheme not in {"http", "https"}
    or not url.hostname
    or url.username
    or url.password
    or url.path not in {"", "/"}
    or url.query
    or url.fragment
):
    raise SystemExit("PUBLIC_URL must look like http://host or https://host without a path")
print(url.hostname)
PY
)"

NEW_CONFIG=0
if [[ ! -f $BACKEND_ENV || $FORCE_CONFIG == "1" ]]; then
  NEW_CONFIG=1
  DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -hex 24)}"
  JWT_SECRET_KEY="${JWT_SECRET_KEY:-$(openssl rand -hex 48)}"
  INITIAL_ADMIN_PASSWORD="${INITIAL_ADMIN_PASSWORD:-$(openssl rand -hex 12)}"
  INITIAL_EMPLOYEE_PASSWORD="${INITIAL_EMPLOYEE_PASSWORD:-$(openssl rand -hex 12)}"
  ENCODED_DB_PASSWORD="$(python3.11 - "$DB_PASSWORD" <<'PY'
import sys
from urllib.parse import quote
print(quote(sys.argv[1], safe=""))
PY
)"

  install -m 0600 -o "$APP_USER" -g "$APP_GROUP" /dev/null "$BACKEND_ENV"
  cat >"$BACKEND_ENV" <<EOF
APP_NAME=Internal Content Publish Platform
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+psycopg://${DB_USER}:${ENCODED_DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}
TEST_DATABASE_URL=postgresql+psycopg://${DB_USER}:${ENCODED_DB_PASSWORD}@127.0.0.1:5432/${TEST_DB_NAME}
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
  chown "$APP_USER:$APP_GROUP" "$BACKEND_ENV"
  chmod 0600 "$BACKEND_ENV"
else
  echo "Preserving existing ${BACKEND_ENV}. Use FORCE_CONFIG=1 to regenerate it."
fi

echo "[4/12] Creating PostgreSQL role and databases..."
ROLE_EXISTS="$(runuser -u postgres -- psql -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | tr -d '[:space:]')"
if [[ $NEW_CONFIG == "1" || -n ${DB_PASSWORD:-} ]]; then
  ACTIVE_DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD is required to create or update the database role}"
  runuser -u postgres -- psql -d postgres -v ON_ERROR_STOP=1 \
    --set=role_name="$DB_USER" --set=role_password="$ACTIVE_DB_PASSWORD" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'role_name', :'role_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'role_name')
\gexec
SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'role_name', :'role_password')
\gexec
SQL
elif [[ $ROLE_EXISTS != "1" ]]; then
  echo "Database role ${DB_USER} is missing. Rerun with DB_PASSWORD set." >&2
  exit 1
fi

runuser -u postgres -- psql -d postgres -v ON_ERROR_STOP=1 \
  --set=db_name="$DB_NAME" --set=role_name="$DB_USER" <<'SQL'
SELECT format('CREATE DATABASE %I OWNER %I', :'db_name', :'role_name')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_name')
\gexec
SQL

if [[ $RUN_TESTS == "1" ]]; then
  runuser -u postgres -- psql -d postgres -v ON_ERROR_STOP=1 \
    --set=db_name="$TEST_DB_NAME" --set=role_name="$DB_USER" <<'SQL'
SELECT format('CREATE DATABASE %I OWNER %I', :'db_name', :'role_name')
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'db_name')
\gexec
SQL
fi

echo "[5/12] Installing backend dependencies in a Python 3.11 virtual environment..."
if [[ ! -x $VENV_ROOT/bin/python ]]; then
  runuser -u "$APP_USER" -- python3.11 -m venv "$VENV_ROOT"
fi
runuser -u "$APP_USER" -- "$VENV_ROOT/bin/python" -m pip install --upgrade pip setuptools wheel
runuser -u "$APP_USER" -- "$VENV_ROOT/bin/python" -m pip install -r "$BACKEND_ROOT/requirements.txt"

echo "[6/12] Building the Vue frontend with Node.js $(node --version)..."
runuser -u "$APP_USER" -- npm --prefix "$APP_ROOT" ci
runuser -u "$APP_USER" -- env VITE_API_BASE_URL=/api VITE_USE_MOCK=false npm --prefix "$APP_ROOT" run build

echo "[7/12] Applying database migrations..."
runuser -u "$APP_USER" -- env PYTHONPATH="$BACKEND_ROOT" \
  "$VENV_ROOT/bin/python" -m alembic -c "$BACKEND_ROOT/alembic.ini" upgrade head

ADMIN_EXISTED="$(runuser -u postgres -- psql -d "$DB_NAME" -tAc "SELECT 1 FROM users WHERE username='admin' LIMIT 1" | tr -d '[:space:]')"
EMPLOYEE_EXISTED="$(runuser -u postgres -- psql -d "$DB_NAME" -tAc "SELECT 1 FROM users WHERE username='employee' LIMIT 1" | tr -d '[:space:]')"
INITIAL_ADMIN_PASSWORD="${INITIAL_ADMIN_PASSWORD:-$(openssl rand -hex 12)}"
INITIAL_EMPLOYEE_PASSWORD="${INITIAL_EMPLOYEE_PASSWORD:-$(openssl rand -hex 12)}"
runuser -u "$APP_USER" -- env PYTHONPATH="$BACKEND_ROOT" \
  SEED_ADMIN_PASSWORD="$INITIAL_ADMIN_PASSWORD" SEED_EMPLOYEE_PASSWORD="$INITIAL_EMPLOYEE_PASSWORD" \
  "$VENV_ROOT/bin/python" "$BACKEND_ROOT/scripts/seed.py"

if [[ $RUN_TESTS == "1" ]]; then
  echo "[8/12] Running backend tests against ${TEST_DB_NAME}..."
  runuser -u "$APP_USER" -- env PYTHONPATH="$BACKEND_ROOT" \
    "$VENV_ROOT/bin/python" -m pytest "$BACKEND_ROOT/tests" -q
else
  echo "[8/12] Backend tests skipped. Use RUN_TESTS=1 to enable them."
fi

echo "[9/12] Installing frontend build output..."
install -d -m 0755 -o root -g root "$WEB_ROOT"
rsync -a --delete "$APP_ROOT/dist/" "$WEB_ROOT/"
chown -R root:root "$WEB_ROOT"
find "$WEB_ROOT" -type d -exec chmod 0755 {} +
find "$WEB_ROOT" -type f -exec chmod 0644 {} +

echo "[10/12] Installing systemd and Nginx configuration..."
cat >/etc/systemd/system/content-publish.service <<EOF
[Unit]
Description=Internal Content Publish Platform API
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=${APP_USER}
Group=${APP_GROUP}
WorkingDirectory=${BACKEND_ROOT}
ExecStart=${VENV_ROOT}/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers ${UVICORN_WORKERS} --proxy-headers --forwarded-allow-ips=127.0.0.1
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=${DATA_ROOT}

[Install]
WantedBy=multi-user.target
EOF

cat >/etc/nginx/conf.d/content-publish.conf <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${PUBLIC_HOST};

    root ${WEB_ROOT};
    index index.html;
    client_max_body_size $((MAX_UPLOAD_SIZE_MB + 10))m;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 720s;
        proxy_send_timeout 720s;
    }

    location /published/ {
        alias ${DATA_ROOT}/published/;
        index index.html;
        autoindex off;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location ~ /\\.(?!well-known/) {
        deny all;
    }
}
EOF

if command -v getenforce >/dev/null 2>&1 && [[ $(getenforce) != "Disabled" ]]; then
  setsebool -P httpd_can_network_connect 1
  semanage fcontext -a -t httpd_sys_content_t "${WEB_ROOT}(/.*)?" 2>/dev/null || \
    semanage fcontext -m -t httpd_sys_content_t "${WEB_ROOT}(/.*)?"
  semanage fcontext -a -t httpd_sys_content_t "${DATA_ROOT}/published(/.*)?" 2>/dev/null || \
    semanage fcontext -m -t httpd_sys_content_t "${DATA_ROOT}/published(/.*)?"
  restorecon -RF "$WEB_ROOT" "$DATA_ROOT/published"
fi

nginx -t
systemctl daemon-reload
systemctl enable --now content-publish.service nginx.service
systemctl restart content-publish.service nginx.service

echo "[11/12] Configuring the firewall..."
if systemctl is-active --quiet firewalld.service; then
  firewall-cmd --permanent --add-service=http
  firewall-cmd --permanent --add-service=https
  firewall-cmd --reload
fi

echo "[12/12] Verifying services..."
for _ in {1..30}; do
  if curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS http://127.0.0.1:8000/api/health >/dev/null
curl -fsS -H "Host: ${PUBLIC_HOST}" http://127.0.0.1/api/health >/dev/null

echo
echo "Deployment completed successfully."
echo "Site:       ${PUBLIC_URL}/"
echo "Health:     ${PUBLIC_URL}/api/health"
echo "App root:   ${APP_ROOT}"
echo "Data root:  ${DATA_ROOT}"
echo "Logs:       journalctl -u content-publish -f"
if [[ $ADMIN_EXISTED != "1" ]]; then
  echo "Initial admin:    admin / ${INITIAL_ADMIN_PASSWORD}"
fi
if [[ $EMPLOYEE_EXISTED != "1" ]]; then
  echo "Initial employee: employee / ${INITIAL_EMPLOYEE_PASSWORD}"
fi
echo "Store any displayed initial passwords securely; they are not written to backend/.env."
