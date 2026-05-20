#!/usr/bin/env bash
set -euo pipefail

CONFIG_FILE="${CONFIG_FILE:-/etc/word-collection-staging.env}"

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "Missing staging config file: ${CONFIG_FILE}"
  echo "Create it with at least: DOMAIN, DB_PASSWORD, OPENAI_API_KEY"
  exit 1
fi

set -a
source "${CONFIG_FILE}"
set +a

export REPO_URL="${REPO_URL:-git@github.com:HaydenProMax/WordCollection.git}"
export DOMAIN="${DOMAIN:-}"
export APP_NAME="word-collection-staging"
export APP_USER="word-collection-staging"
export APP_HOME="/opt/word-collection-staging"
export APP_PORT="8001"
export APP_REF="test"
export DB_NAME="word_collection_staging"
export DB_USER="word_collection_staging"
export DB_PASSWORD="${DB_PASSWORD:-}"
export MODEL_PROVIDER="${MODEL_PROVIDER:-openai}"
export OPENAI_MODEL="${OPENAI_MODEL:-gpt-5.5}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://www.fhl.mom/v1}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
export ENABLE_HTTPS="${ENABLE_HTTPS:-0}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/deploy-ubuntu-24.04.sh"
