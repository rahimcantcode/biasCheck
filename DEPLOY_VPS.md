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
npm ci
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
cd frontend && npm ci && npm run build
cd /var/www/biasCheck/backend && bash setup_env.sh
sudo systemctl restart biascheck-backend.service
sudo systemctl restart biascheck-frontend.service
sudo systemctl reload nginx
```


## Experimental political entailment engine

This branch includes an opt-in PoliticalDEBATE large engine. It is a functioning
experimental assessment pipeline, not an independently validated high-accuracy
release. The default remains the original RoBERTa engine. Do not create an
approved decision policy based on the development results.

From the repository root, after backend setup:

```bash
backend/.venv/bin/python backend/download_nli_model.py
```

The downloader pins the model revision and verifies SHA-256 for weights,
configuration, and tokenizer files. It requires about 1.75 GB for the checkpoint.
Keep additional free disk space for downloads and dependencies. The development
machine has 8 GB RAM; production capacity and latency must be measured on your VPS.
Use one backend worker. Multiple workers duplicate the model in memory.

Set these in `backend/.env` to enable the candidate:

```env
BIASCHECK_ENGINE=political_nli
BIASCHECK_NLI_MODEL_DIR=/var/www/biasCheck/research/checkpoints/political-debate-large
BIASCHECK_TORCH_THREADS=2
```

Build and restart both services with the updated nginx timeout. `/api/health`
must report `engine: political_nli`, the pinned model revision, and
`release_approved: false`. That false value is intentional: results are tentative.
Try a dinner description, a clear policy position, and a one-word input. They
should produce distinct relevance/context outcomes instead of universal Left.
Inspect all three analysis modes. CPU inference can take minutes on long articles.
The candidate rejects more than 12 windows per text or more than 20 passages.
Concurrent requests receive a retryable busy response instead of running multiple
large inference jobs at once.

Rollback: set `BIASCHECK_ENGINE=roberta` and restart the backend. Keep the original
checkpoint available. The frontend understands both response formats. This is
not a substitute for retaining your last known working deployment and configuration.

URL retrieval connects directly to a checked public IP address, verifies TLS
against the requested hostname, and rechecks redirects. Private and link-local
addresses are rejected. Deployment egress restrictions remain useful defense in
depth. Sites that block automated retrieval require pasted text.
No change in this branch has been deployed to the VPS from this workspace.

## Investor demonstration mode

To make the live interface display clear RoBERTa estimates, add this setting to
`backend/.env`:

```env
BIASCHECK_DEMO_MODE=1
```

Restart only the backend after changing the setting. The interface labels the
result `Experimental estimate`; `/health` still reports `release_approved: false`.
Short and ambiguous text remains unlabelled. Remove the setting and restart to
restore the research-safe behavior.
