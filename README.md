# Bias Checker

Bias Checker is a full-stack app for analyzing political bias in news content using a fine-tuned RoBERTa classifier stored in `bias_model/`.

## Project Structure

```text
bias_app/
  backend/
  frontend/
  bias_model/
```

## Local Development

### Backend

Create and activate a virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If your exported `tokenizer.json` hits a compatibility error, use the bundled setup helper instead:

```bash
cd backend
bash setup_env.sh
```

Run the API locally:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend URL:

```text
http://localhost:8000
```

### Frontend

Install dependencies:

```bash
cd frontend
npm install
```

Run the Next.js app:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

## Production Deployment

This repo is prepared for single-VPS deployment with:

- FastAPI on `127.0.0.1:8000`
- Next.js on `127.0.0.1:3000`
- nginx reverse proxying `/api/` to the backend and `/` to the frontend
- systemd managing both services

See [`DEPLOY_VPS.md`](/Users/rahim/Documents/bias_app/DEPLOY_VPS.md) for the full Hostinger VPS deployment guide.

## Notes

- The backend loads the exported Hugging Face model from `../bias_model`.
- The bundled `backend/setup_env.sh` applies a tokenizer compatibility fix for this exported model on Python 3.11 + local CPU PyTorch.
- In local browser development, the frontend falls back to `http://localhost:8000`.
- In production, the frontend can use same-origin `/api` behind nginx.
- To override the frontend API target explicitly, set `NEXT_PUBLIC_API_BASE_URL`.
