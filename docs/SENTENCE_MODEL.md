# Sentence-only pretrained model integration

## Behavior

- One article input and Analyze button; no article/paragraph mode selector.
- pySBD splits sentences with exact Unicode offsets. Paragraph breaks and original
  pasted text are preserved.
- DeBERTa predicts LEFT/CENTER/RIGHT for complete sentences in small batches.
- Model-card mapping: 0=LEFT, 1=CENTER, 2=RIGHT. The upstream config uses generic
  LABEL_0/LABEL_1/LABEL_2, so the mapping is explicitly recorded in the manifest.
- Each sentence has one vote. The article summary reports counts, shares and the
  most frequent label. Ties remain ties.
- No phrase extraction, neutral-text filter, generated rationale, retraining or
  additional model is used.
- At most 300 sentences and 100,000 characters per request. An individual sentence
  over 512 model tokens is rejected explicitly, never silently truncated.
- The backend accepts old mode names for client compatibility but always responds
  with sentence mode. The updated frontend requires the new summary contract.

## Selection and verification

The initial PoliticalBiasBERT candidate returned RIGHT on all six varied smoke
sentences, including opposing positions. Its tokenizer vocabulary and label
mapping were checked. It was not selected.

Selected: Matous Volf and Jakub Simko's
[political-leaning-deberta-large](https://huggingface.co/matous-volf/political-leaning-deberta-large).
The exact model and tokenizer revisions are in `backend/political_checkpoint.json`.

The six manually written smoke examples exercise integration, not independent
model accuracy. DeBERTa distinguishes the opposing political examples, but labels
“Congress passed the bill on Tuesday.” as LEFT. The known neutral-text error is
retained in `sentence-model-smoke.json`; no accuracy percentage is claimed.
The author's recommendation to filter nonpolitical input is not implemented in
this deliberately direct classifier flow.

The test runtime used Python 3.12, torch 2.6.0+cpu and transformers 4.57.1.
Backend tests check count aggregation, ties, Unicode/repeated sentences,
abbreviations, exact source preservation, old-client modes and input limits.
The Next.js production build and TypeScript checks verify the client contract.
Eight backend tests and two rendered React/Unicode tests passed. The rendered
React test uses the saved real-model response to verify sentence colors and counts.
An interactive browser check could not run because the Chromium download failed;
no desktop/mobile visual inspection is claimed.

## Attribution

Model: *Political Leaning and Politicalness Classification of Texts*,
Matous Volf and Jakub Simko (2025).
[Paper](https://arxiv.org/abs/2507.13913) ·
[Source](https://github.com/matous-volf/political-leaning-prediction) ·
[Model license](https://creativecommons.org/licenses/by-nc/4.0/).

Published weights are unmodified. Application integration and sentence-vote
aggregation are new. The model license requires attribution and noncommercial use.
The user's stated purpose is a noncommercial school project.

## Updating the VPS

Run from an authenticated VPS terminal. This update was prepared on a separate
branch; it has not been deployed by the assistant.

First check for local changes:

```bash
cd /var/www/biasCheck
git status --short
```

If tracked files have local edits, preserve/reconcile them before switching.
Do not discard server-specific changes.

```bash
git fetch origin feature/sentence-bias-2026-10-04
git switch feature/sentence-bias-2026-10-04
cp backend/.env backend/.env.before-sentence-model
```

Set this line in `backend/.env`, keeping the other settings:

```env
BIASCHECK_MODEL_DIR=/var/www/biasCheck/models/political-leaning
```

Prepare the dependencies, model and frontend before restarting services:

```bash
cd /var/www/biasCheck/backend
bash setup_env.sh
cd /var/www/biasCheck/frontend
npm ci
NEXT_PUBLIC_API_BASE_URL=/api npm run build
sudo chown -R www-data:www-data /var/www/biasCheck/models/political-leaning
sudo systemctl restart biascheck-backend biascheck-frontend
curl --fail http://127.0.0.1:8000/health
```

The health response must name `matous-volf/political-leaning-deberta-large`.
For long articles, set `proxy_read_timeout 300s;` and `proxy_send_timeout 300s;`
inside the existing Nginx `/api/` location, then run `sudo nginx -t` and
`sudo systemctl reload nginx`. Preserve the server's real domain and TLS settings.
Then open the website, analyze a short article, and check that sentence totals
match the number of colored sentences. Check RAM before installing the larger
model; its weight file alone is about 1.74 GB. The local runtime's speed is not a
VPS latency guarantee.
