# Bias Checker

## Project overview

Bias Checker is a full-stack political bias analysis app built with:

- FastAPI backend
- Next.js App Router frontend
- a local Hugging Face model stored in `bias_model/`

This research branch analyzes full article context and exposes experimental model scores. Reliable political labels are withheld until a model-bound policy passes independent evaluation. This behavior does not make the underlying model more accurate.

## Article reading experience

- UTF-8 `.txt` upload and pasted text preserve exact Unicode and whitespace. Supported experimental phrase evidence appears blue for LEFT and red for RIGHT, with neutral text unchanged.
- Phrase evidence uses a separate disabled-by-default provider. The new self-hosted adapter still needs a rights-cleared model, capacity testing and independent span validation. No phrase model has passed those gates. See [phrase evidence status and setup](research/PHRASE_EVIDENCE.md).
- Article mode now requests article inference. Overall results are computed from the document, independently of passage scores.
- Long documents use overlapping windows with explicit token coverage. Inputs exceeding the processing limit are rejected rather than silently truncated.
- Sentence and paragraph modes preserve exact text offsets. Their scores remain experimental until separately validated.
- Unapproved or uncertain results have no political label or partisan coloring. Raw scores are available as experimental diagnostics, not probabilities of correctness.
- Backend response version 0.4 includes `overall`, nullable labels, offsets, warnings, coverage, model hashes and source-bound experimental evidence spans. Deploy frontend and backend together; older clients do not implement the phrase contract.

See [research workflow](research/README.md) and [experiment log](research/EXPERIMENT_LOG.md). No newly validated model or production deployment is claimed.

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

For the pinned CPU runtime without modifying installed package checks:

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
npm ci
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
npm ci
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


## Experimental replacement model

The original RoBERTa remains the default. To run the new, pinned PoliticalDEBATE
large candidate locally, from the repository root:

```bash
backend/.venv/bin/python backend/download_nli_model.py
BIASCHECK_ENGINE=political_nli backend/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Use a single worker. This candidate returns a relevance/context assessment and,
when development thresholds permit, a **tentative** Left, Right, or Center result.
`label` remains null and `release_approved` remains false. Tentative results are
visible in the interface; passage diagnostics are available under a separate
expander. Independent entailment scores do not form a probability distribution.
Center here means political reporting without an expressed side, not objectivity.

This is an experimental text-position model, not a verified detector of media
bias, loaded language, factual accuracy, or a publisher's ideology. Known failures
include vague policy criticism, sarcasm, and mixtures of positions. See
[implementation and validation notes](research/NLI_IMPLEMENTATION.md) before
choosing the engine. No VPS deployment or high-accuracy release is claimed.

## Investor demonstration mode

For a product demonstration, set `BIASCHECK_DEMO_MODE=1` in the backend `.env`
and restart the backend. The original RoBERTa engine will display sufficiently
clear model estimates and keep short or ambiguous inputs unlabelled. The page
marks every displayed result as an experimental estimate, and `/health` continues
to report `release_approved: false`. This mode is for demonstrating the product
workflow and should not be presented as independently validated accuracy.
