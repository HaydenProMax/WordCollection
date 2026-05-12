# Test Environment Deployment

This document describes how to deploy a server-side test environment from the `test` branch.

The test environment should be isolated from production:

- Branch: `test`
- App name: `encollect-test`
- App home: `/opt/encollect-test`
- App port: `8001`
- Database: `encollect_test`
- Service: `encollect-test`
- Recommended domain: `test.your-domain.example.com`

Do not share the production database with the test environment.

## 1. Ensure the `test` Branch Exists Remotely

From local development:

```bash
git checkout test
git push -u origin test
```

## 2. Deploy Test Environment

Run this on the Ubuntu 24.04 server.

Replace:

- `REPO_URL`
- `DOMAIN`
- `DB_PASSWORD`
- `OPENAI_API_KEY`

```bash
sudo -E env \
  REPO_URL='git@github.com:HaydenProMax/WordCollection.git' \
  DOMAIN='test.your-domain.example.com' \
  APP_NAME='encollect-test' \
  APP_USER='encollect-test' \
  APP_HOME='/opt/encollect-test' \
  APP_PORT='8001' \
  APP_REF='test' \
  DB_NAME='encollect_test' \
  DB_USER='encollect_test' \
  DB_PASSWORD='replace_with_a_strong_test_password' \
  OPENAI_MODEL='gpt-5.5' \
  OPENAI_BASE_URL='https://www.fhl.mom/v1' \
  OPENAI_API_KEY='replace_with_your_api_key' \
  ENABLE_HTTPS='1' \
  bash scripts/deploy-ubuntu-24.04.sh
```

`APP_REF=test` tells the script to deploy from the `test` branch instead of a release tag.

## 3. Update Test Environment

After local changes are merged or pushed to `test`, run the deployment script again with the same variables.

The script is designed to be re-runnable:

- It fetches the latest Git refs.
- It checks out `APP_REF`.
- It reinstalls Python dependencies.
- It runs Alembic migrations.
- It restarts the systemd service.
- It reloads Nginx.

## 4. Check Services

```bash
sudo systemctl status encollect-test
sudo journalctl -u encollect-test -f
curl http://127.0.0.1:8001/api/lookups
```

## 5. Promote Test to Production

After the test environment is verified:

```bash
git checkout main
git merge --ff-only test
git tag -a vX.Y.Z -m "vX.Y.Z release"
git push origin main
git push origin vX.Y.Z
```

Production should deploy a stable tag such as `v1.0.0`, not the moving `test` branch.
