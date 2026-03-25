# Bias Checker

## Project overview

Bias Checker is a full-stack political bias analysis app built with:

- FastAPI backend
- Next.js App Router frontend
- a local Hugging Face model stored in `bias_model/`

The app classifies pasted article text or extracted URL content as `LEFT`, `RIGHT`, or `CENTER`, with support for article-level, sentence-level, and paragraph-level analysis.

Production is live at:

- Main site: `https://bias.r4him.tech`
- Backend health endpoint: `https://bias.r4him.tech/api/health`

Production routing is:

- `/` serves the frontend UI
- `/api/*` serves backend API routes through nginx

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the exported tokenizer needs the compatibility fix used in production:

```bash
cd backend
bash setup_env.sh
```

Run the API locally:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Local backend URL:

```text
http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Local frontend URL:

```text
http://localhost:3000
```

Notes:

- In local browser development, the frontend falls back to `http://localhost:8000`.
- To override the frontend API target, set `NEXT_PUBLIC_API_BASE_URL`.

## Production deployment overview

Bias Checker is deployed on a single Hostinger VPS with:

- FastAPI backend on `127.0.0.1:8000`
- Next.js frontend on `127.0.0.1:3000`
- nginx reverse proxy
- systemd services for both backend and frontend
- HTTPS managed by Certbot
- domain: `https://bias.r4him.tech`

Production app path on the VPS:

```text
/var/www/biasCheck
```

The deployment uses:

- nginx to proxy `/` to the frontend
- nginx to proxy `/api/` to the backend
- systemd so both services restart automatically after reboot

See [`DEPLOY_VPS.md`](/Users/rahim/Documents/bias_app/DEPLOY_VPS.md) for the full VPS deployment guide.

## VPS deployment notes

The production deployment included these steps:

1. Cloned the repo to `/var/www/biasCheck`
2. Installed system packages for Python, Node.js, nginx, curl, and git
3. Created `backend/.venv`
4. Installed backend dependencies from `requirements.txt`
5. Applied the tokenizer compatibility fix so the exported tokenizer could load
6. Installed Git LFS and ran `git lfs pull`
7. Verified `bias_model/model.safetensors` was the real model file, not an LFS pointer
8. Tested the backend with `uvicorn`
9. Built and tested the frontend with Next.js
10. Enabled permanent background services with systemd
11. Configured nginx to route `/` to the frontend and `/api/` to the backend
12. Pointed DNS for `bias.r4him.tech` to the VPS
13. Issued and installed HTTPS with Certbot

Important notes:

- The backend systemd service expects this file to exist:
  `/var/www/biasCheck/backend/.env`
- Even if it is empty, create it. The backend service initially failed because the `.env` file referenced by systemd did not exist, and creating `backend/.env` fixed it.
- The model file `bias_model/model.safetensors` is stored with Git LFS.
- After cloning or pulling updates, always run:

```bash
git lfs pull
```

## Updating the production server

Run:

```bash
cd /var/www/biasCheck
git pull
git lfs pull

cd /var/www/biasCheck/backend
source .venv/bin/activate
pip install -r requirements.txt

cd /var/www/biasCheck/frontend
npm install
export NEXT_PUBLIC_API_BASE_URL=/api
npm run build

systemctl restart biascheck-backend
systemctl restart biascheck-frontend
systemctl reload nginx
```

If needed, make sure the backend `.env` file still exists:

```bash
touch /var/www/biasCheck/backend/.env
```

## Troubleshooting

Check service status:

```bash
systemctl status biascheck-backend --no-pager
systemctl status biascheck-frontend --no-pager
```

Check recent service logs:

```bash
journalctl -u biascheck-backend -n 100 --no-pager
journalctl -u biascheck-frontend -n 100 --no-pager
journalctl -u nginx -n 50 --no-pager
```

Useful checks:

- If backend requests fail, confirm `/api/health` responds.
- If the backend service fails on boot, verify `/var/www/biasCheck/backend/.env` exists.
- If model loading fails after a fresh clone or pull, run `git lfs pull` and confirm `bias_model/model.safetensors` is the actual model file.
- If the frontend loads but analysis fails, confirm nginx is routing `/api/*` to the backend and that the frontend was built with `NEXT_PUBLIC_API_BASE_URL=/api`.
