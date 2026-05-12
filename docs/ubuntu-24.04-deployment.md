# Ubuntu 24.04 Production Deployment

This document describes how to deploy enCollect on Ubuntu 24.04 with:

- FastAPI served by `systemd`
- Nginx as reverse proxy
- Native PostgreSQL on the server
- No Docker database in production

## 1. Install System Dependencies

```bash
sudo apt update
sudo apt install -y \
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
```

Check versions:

```bash
python3 --version
psql --version
nginx -v
```

## 2. Create Application User

Use a dedicated Linux user for the app:

```bash
sudo adduser --system --group --home /opt/encollect encollect
```

## 3. Deploy Code

Clone or copy the repository to `/opt/encollect/app`.

Example with Git:

```bash
sudo -u encollect git clone <your-repo-url> /opt/encollect/app
cd /opt/encollect/app
sudo -u encollect git checkout v1.0.0
```

If the code is copied manually, ensure ownership is correct:

```bash
sudo chown -R encollect:encollect /opt/encollect
```

## 4. Configure PostgreSQL

Create the database user and database:

```bash
sudo -u postgres psql
```

Inside `psql`:

```sql
CREATE USER encollect WITH PASSWORD 'replace_with_a_strong_password';
CREATE DATABASE encollect OWNER encollect;
GRANT ALL PRIVILEGES ON DATABASE encollect TO encollect;
\q
```

The production database connection will use local PostgreSQL:

```text
postgresql+psycopg://encollect:replace_with_a_strong_password@127.0.0.1:5432/encollect
```

## 5. Configure Environment

Create `/opt/encollect/app/.env`:

```bash
sudo -u encollect nano /opt/encollect/app/.env
```

Example:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://encollect:replace_with_a_strong_password@127.0.0.1:5432/encollect
MODEL_PROVIDER=openai
OPENAI_MODEL=gpt-5.5
OPENAI_BASE_URL=https://www.fhl.mom/v1
OPENAI_API_KEY=replace_with_your_api_key
```

Keep `.env` only on the server. Do not commit it.

## 6. Install Python Dependencies

```bash
cd /opt/encollect/app
sudo -u encollect python3 -m venv .venv
sudo -u encollect /opt/encollect/app/.venv/bin/pip install -r backend/requirements.txt
```

## 7. Run Database Migrations

```bash
cd /opt/encollect/app/backend
sudo -u encollect /opt/encollect/app/.venv/bin/python -m alembic upgrade head
```

## 8. Create systemd Service

Create `/etc/systemd/system/encollect.service`:

```bash
sudo nano /etc/systemd/system/encollect.service
```

Content:

```ini
[Unit]
Description=enCollect FastAPI service
After=network.target postgresql.service

[Service]
User=encollect
Group=encollect
WorkingDirectory=/opt/encollect/app/backend
EnvironmentFile=/opt/encollect/app/.env
ExecStart=/opt/encollect/app/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable encollect
sudo systemctl start encollect
sudo systemctl status encollect
```

Check logs:

```bash
sudo journalctl -u encollect -f
```

## 9. Configure Nginx

Create `/etc/nginx/sites-available/encollect`:

```bash
sudo nano /etc/nginx/sites-available/encollect
```

Replace `your-domain.example.com` with your domain:

```nginx
server {
    listen 80;
    server_name your-domain.example.com;

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/encollect /etc/nginx/sites-enabled/encollect
sudo nginx -t
sudo systemctl reload nginx
```

## 10. Configure Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 11. Enable HTTPS

Make sure the domain points to the server IP first.

```bash
sudo certbot --nginx -d your-domain.example.com
```

Verify renewal:

```bash
sudo certbot renew --dry-run
```

## 12. Release Update Procedure

When deploying a new tag:

```bash
cd /opt/encollect/app
sudo -u encollect git fetch --tags
sudo -u encollect git checkout <tag>
sudo -u encollect /opt/encollect/app/.venv/bin/pip install -r backend/requirements.txt
cd /opt/encollect/app/backend
sudo -u encollect /opt/encollect/app/.venv/bin/python -m alembic upgrade head
sudo systemctl restart encollect
sudo systemctl status encollect
```

## 13. Rollback Procedure

Rollback to a previous tag:

```bash
cd /opt/encollect/app
sudo -u encollect git checkout <previous-tag>
cd /opt/encollect/app/backend
sudo -u encollect /opt/encollect/app/.venv/bin/python -m alembic downgrade -1
sudo systemctl restart encollect
```

Only run `alembic downgrade` if the release being rolled back introduced a database migration.

## 14. Backup PostgreSQL

Manual backup:

```bash
sudo -u postgres pg_dump encollect > /opt/encollect/backup-$(date +%F).sql
sudo chown encollect:encollect /opt/encollect/backup-$(date +%F).sql
```

Restore backup:

```bash
sudo -u postgres psql encollect < /opt/encollect/backup-YYYY-MM-DD.sql
```

## 15. Health Checks

Check application:

```bash
curl -I http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/lookups
```

Check services:

```bash
sudo systemctl status encollect
sudo systemctl status nginx
sudo systemctl status postgresql
```

