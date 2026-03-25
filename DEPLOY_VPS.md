# Deploy Bias Checker on a Single VPS

This guide deploys Bias Checker to one Hostinger VPS with:

- FastAPI backend on `127.0.0.1:8000`
- Next.js frontend on `127.0.0.1:3000`
- nginx reverse proxy
- one public domain or subdomain
- systemd for process management

The examples below assume the app lives at:

```bash
/var/www/biasCheck
```

## 1. Point DNS to the VPS

In Hostinger DNS:

- create an `A` record for your domain or subdomain
- point it to your VPS public IP
- wait for DNS to propagate

Examples:

- `biascheck.yourdomain.com -> VPS_IP`
- `yourdomain.com -> VPS_IP`

## 2. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm nginx certbot python3-certbot-nginx git git-lfs
git lfs install
```

If you prefer a newer Node version than the distro default, install Node 20 before continuing.

## 3. Clone the repo

```bash
sudo mkdir -p /var/www
sudo chown -R $USER:$USER /var/www
cd /var/www
git clone https://github.com/rahimcantcode/biasCheck.git
cd biasCheck
git lfs pull
```

## 4. Backend setup

```bash
cd /var/www/biasCheck/backend
bash setup_env.sh
cp .env.example .env
```

Edit `.env` if needed:

```bash
nano /var/www/biasCheck/backend/.env
```

Recommended production values:

```env
BIASCHECK_ENV=production
BIASCHECK_MODEL_DIR=/var/www/biasCheck/bias_model
BIASCHECK_ALLOWED_ORIGINS=
BIASCHECK_BACKEND_HOST=127.0.0.1
BIASCHECK_BACKEND_PORT=8000
BIASCHECK_REQUEST_TIMEOUT=10
```

## 5. Frontend setup

```bash
cd /var/www/biasCheck/frontend
npm install
```

Optional frontend environment file:

```bash
cat <<'EOF' > /var/www/biasCheck/frontend/.env.production
NEXT_PUBLIC_API_BASE_URL=/api
EOF
```

## 6. Build the frontend

```bash
cd /var/www/biasCheck/frontend
npm run build
```

## 7. Install systemd services

Copy the service files:

```bash
sudo cp /var/www/biasCheck/deploy/systemd/biascheck-backend.service /etc/systemd/system/
sudo cp /var/www/biasCheck/deploy/systemd/biascheck-frontend.service /etc/systemd/system/
```

Make sure the service user can read the app:

```bash
sudo chown -R www-data:www-data /var/www/biasCheck
```

Reload and enable services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable biascheck-backend.service
sudo systemctl enable biascheck-frontend.service
sudo systemctl start biascheck-backend.service
sudo systemctl start biascheck-frontend.service
```

Check status:

```bash
sudo systemctl status biascheck-backend.service
sudo systemctl status biascheck-frontend.service
```

## 8. Configure nginx

Copy the nginx config:

```bash
sudo cp /var/www/biasCheck/deploy/nginx/biascheck.conf /etc/nginx/sites-available/biascheck.conf
```

Edit the `server_name` line to match your real domain or subdomain:

```bash
sudo nano /etc/nginx/sites-available/biascheck.conf
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/biascheck.conf /etc/nginx/sites-enabled/biascheck.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 9. Enable SSL with Certbot

After DNS is pointing correctly and nginx is serving HTTP:

```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

For a subdomain, use only that host:

```bash
sudo certbot --nginx -d biascheck.yourdomain.com
```

Test renewal:

```bash
sudo certbot renew --dry-run
```

## 10. Verify the deployment

Backend health:

```bash
curl http://127.0.0.1:8000/health
```

Public site:

```bash
curl -I https://your-domain.com
```

In a browser, open your domain and confirm:

- the homepage loads
- analysis requests succeed
- `/api/predict` is routed through nginx to FastAPI

## Updating later

When you push new code:

```bash
cd /var/www/biasCheck
git pull
git lfs pull
cd frontend && npm install && npm run build
cd /var/www/biasCheck/backend && bash setup_env.sh
sudo systemctl restart biascheck-backend.service
sudo systemctl restart biascheck-frontend.service
sudo systemctl reload nginx
```
