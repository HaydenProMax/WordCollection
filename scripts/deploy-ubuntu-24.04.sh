#!/usr/bin/env bash
set -euo pipefail

APP_NAME="${APP_NAME:-encollect}"
APP_USER="${APP_USER:-encollect}"
APP_HOME="${APP_HOME:-/opt/encollect}"
APP_DIR="${APP_DIR:-${APP_HOME}/app}"
APP_PORT="${APP_PORT:-8000}"
APP_TAG="${APP_TAG:-v1.0.0}"

REPO_URL="${REPO_URL:-}"
DOMAIN="${DOMAIN:-}"
ENABLE_HTTPS="${ENABLE_HTTPS:-0}"

DB_NAME="${DB_NAME:-encollect}"
DB_USER="${DB_USER:-encollect}"
DB_PASSWORD="${DB_PASSWORD:-}"

MODEL_PROVIDER="${MODEL_PROVIDER:-openai}"
OPENAI_MODEL="${OPENAI_MODEL:-gpt-5.5}"
OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://www.fhl.mom/v1}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"

SYSTEMD_SERVICE="/etc/systemd/system/${APP_NAME}.service"
NGINX_SITE="/etc/nginx/sites-available/${APP_NAME}"
NGINX_SITE_LINK="/etc/nginx/sites-enabled/${APP_NAME}"

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run this script as root, for example: sudo -E bash scripts/deploy-ubuntu-24.04.sh"
    exit 1
  fi
}

require_config() {
  local missing=()
  [[ -z "${REPO_URL}" ]] && missing+=("REPO_URL")
  [[ -z "${DOMAIN}" ]] && missing+=("DOMAIN")
  [[ -z "${DB_PASSWORD}" ]] && missing+=("DB_PASSWORD")
  [[ -z "${OPENAI_API_KEY}" ]] && missing+=("OPENAI_API_KEY")

  if (( ${#missing[@]} > 0 )); then
    echo "Missing required environment variables: ${missing[*]}"
    echo "Example:"
    echo "sudo -E env REPO_URL='https://github.com/you/enCollect.git' DOMAIN='example.com' DB_PASSWORD='strong-password' OPENAI_API_KEY='key' bash scripts/deploy-ubuntu-24.04.sh"
    exit 1
  fi

  validate_identifier "DB_NAME" "${DB_NAME}"
  validate_identifier "DB_USER" "${DB_USER}"
}

validate_identifier() {
  local name="$1"
  local value="$2"
  if [[ ! "${value}" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
    echo "${name} must match ^[a-zA-Z_][a-zA-Z0-9_]*$"
    exit 1
  fi
}

sql_escape_literal() {
  local value="$1"
  printf "%s" "${value//\'/\'\'}"
}

install_dependencies() {
  apt update
  apt install -y \
    git \
    python3 \
    python3-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    nginx \
    ufw \
    curl \
    ca-certificates \
    certbot \
    python3-certbot-nginx
}

ensure_app_user() {
  if ! id "${APP_USER}" >/dev/null 2>&1; then
    adduser --system --group --home "${APP_HOME}" "${APP_USER}"
  fi
  mkdir -p "${APP_HOME}"
  chown -R "${APP_USER}:${APP_USER}" "${APP_HOME}"
}

deploy_code() {
  if [[ -d "${APP_DIR}/.git" ]]; then
    sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch --tags
  else
    rm -rf "${APP_DIR}"
    sudo -u "${APP_USER}" git clone "${REPO_URL}" "${APP_DIR}"
    sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch --tags
  fi

  sudo -u "${APP_USER}" git -C "${APP_DIR}" checkout "${APP_TAG}"
}

configure_postgres() {
  systemctl enable postgresql
  systemctl start postgresql
  local escaped_db_password
  escaped_db_password="$(sql_escape_literal "${DB_PASSWORD}")"

  if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE USER ${DB_USER} WITH PASSWORD '${escaped_db_password}';"
  else
    sudo -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER USER ${DB_USER} WITH PASSWORD '${escaped_db_password}';"
  fi

  if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
    sudo -u postgres createdb -O "${DB_USER}" "${DB_NAME}"
  fi

  sudo -u postgres psql -v ON_ERROR_STOP=1 -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"
}

write_env_file() {
  cat > "${APP_DIR}/.env" <<EOF
APP_ENV=production
DATABASE_URL=postgresql+psycopg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}
MODEL_PROVIDER=${MODEL_PROVIDER}
OPENAI_MODEL=${OPENAI_MODEL}
OPENAI_BASE_URL=${OPENAI_BASE_URL}
OPENAI_API_KEY=${OPENAI_API_KEY}
EOF
  chown "${APP_USER}:${APP_USER}" "${APP_DIR}/.env"
  chmod 600 "${APP_DIR}/.env"
}

install_python_dependencies() {
  sudo -u "${APP_USER}" python3 -m venv "${APP_DIR}/.venv"
  sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/pip" install --upgrade pip
  sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt"
}

run_migrations() {
  cd "${APP_DIR}/backend"
  sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/python" -m alembic upgrade head
}

write_systemd_service() {
  cat > "${SYSTEMD_SERVICE}" <<EOF
[Unit]
Description=enCollect FastAPI service
After=network.target postgresql.service

[Service]
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}/backend
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port ${APP_PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable "${APP_NAME}"
  systemctl restart "${APP_NAME}"
}

write_nginx_site() {
  cat > "${NGINX_SITE}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

  ln -sfn "${NGINX_SITE}" "${NGINX_SITE_LINK}"
  nginx -t
  systemctl enable nginx
  systemctl reload nginx
}

configure_firewall() {
  ufw allow OpenSSH
  ufw allow 'Nginx Full'
  ufw --force enable
}

configure_https() {
  if [[ "${ENABLE_HTTPS}" == "1" ]]; then
    certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos --redirect --register-unsafely-without-email
  fi
}

health_check() {
  systemctl --no-pager status "${APP_NAME}" || true
  curl -fsS "http://127.0.0.1:${APP_PORT}/" >/dev/null
  echo "Deployment finished. Open: http://${DOMAIN}"
  if [[ "${ENABLE_HTTPS}" == "1" ]]; then
    echo "HTTPS enabled. Open: https://${DOMAIN}"
  fi
}

main() {
  require_root
  require_config
  install_dependencies
  ensure_app_user
  deploy_code
  configure_postgres
  write_env_file
  install_python_dependencies
  run_migrations
  write_systemd_service
  write_nginx_site
  configure_firewall
  configure_https
  health_check
}

main "$@"
