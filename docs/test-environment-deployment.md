# Test Environment Deployment

This document describes how to deploy a server-side test environment from the `test` branch.

The test environment should be isolated from production:

- Branch: `test`
- App name: `word-collection-staging`
- App home: `/opt/word-collection-staging`
- App port: `8001`
- Database: `word_collection_staging`
- Service: `word-collection-staging`
- Recommended domain: `test.your-domain.example.com`

Do not share the production database with the test environment.

## 1. Ensure the `test` Branch Exists Remotely

From local development:

```bash
git checkout test
git push -u origin test
```

## 2. Create Staging Config

Create a private server-side config file:

```bash
sudo nano /etc/word-collection-staging.env
```

Example:

```bash
DOMAIN='test.your-domain.example.com'
DB_PASSWORD='replace_with_a_strong_test_password'
OPENAI_API_KEY='replace_with_your_api_key'
ENABLE_HTTPS='1'
```

Optional overrides:

```bash
REPO_URL='git@github.com:HaydenProMax/WordCollection.git'
OPENAI_MODEL='gpt-5.5'
OPENAI_BASE_URL='https://www.fhl.mom/v1'
```

Protect it:

```bash
sudo chmod 600 /etc/word-collection-staging.env
```

## 3. Deploy Test Environment

Run this from the repository directory on the Ubuntu 24.04 server:

```bash
sudo bash scripts/deploy-staging-ubuntu-24.04.sh
```

The wrapper script fixes the staging values:

```text
APP_NAME=word-collection-staging
APP_USER=word-collection-staging
APP_HOME=/opt/word-collection-staging
APP_PORT=8001
APP_REF=test
DB_NAME=word_collection_staging
DB_USER=word_collection_staging
```

## 4. Manual Deploy Command

The long-form command is still available if you need to override everything manually.

Replace:

- `REPO_URL`
- `DOMAIN`
- `DB_PASSWORD`
- `OPENAI_API_KEY`

```bash
sudo -E env \
  REPO_URL='git@github.com:HaydenProMax/WordCollection.git' \
  DOMAIN='test.your-domain.example.com' \
  APP_NAME='word-collection-staging' \
  APP_USER='word-collection-staging' \
  APP_HOME='/opt/word-collection-staging' \
  APP_PORT='8001' \
  APP_REF='test' \
  DB_NAME='word_collection_staging' \
  DB_USER='word_collection_staging' \
  DB_PASSWORD='replace_with_a_strong_test_password' \
  OPENAI_MODEL='gpt-5.5' \
  OPENAI_BASE_URL='https://www.fhl.mom/v1' \
  OPENAI_API_KEY='replace_with_your_api_key' \
  ENABLE_HTTPS='1' \
  bash scripts/deploy-ubuntu-24.04.sh
```

`APP_REF=test` tells the script to deploy from the `test` branch instead of a release tag.

## 5. Update Test Environment

After local changes are merged or pushed to `test`, run the deployment script again with the same variables.

The script is designed to be re-runnable:

- It fetches the latest Git refs.
- It checks out `APP_REF`.
- It reinstalls Python dependencies.
- It runs Alembic migrations.
- It restarts the systemd service.
- It reloads Nginx.

## 6. Check Services

```bash
sudo systemctl status word-collection-staging
sudo journalctl -u word-collection-staging -f
curl http://127.0.0.1:8001/api/lookups
```

## 7. Promote Test to Production

After the test environment is verified:

```bash
git checkout main
git merge --ff-only test
git tag -a vX.Y.Z -m "vX.Y.Z release"
git push origin main
git push origin vX.Y.Z
```

Production should deploy a stable tag such as `v1.0.0`, not the moving `test` branch.
