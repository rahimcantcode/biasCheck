# Bias Checker

Paste an English news article or URL and select **Analyze**. The app classifies
each sentence as LEFT, CENTER, or RIGHT with an existing pretrained model.
Blue marks left, red marks right, and center keeps the normal text color.

The summary shows sentence counts and percentages. Every sentence counts once;
the most frequent label becomes the overall sentence leaning. A tie is shown as
a tie. Percentages are shares of predicted sentences, not accuracy estimates.

## Model

- [political-leaning-deberta-large](https://huggingface.co/matous-volf/political-leaning-deberta-large), by Matous Volf and Jakub Simko.
- Pinned revision: `36e135e33c24d2a1f6dbdb0eaa774d09e8dfb079`.
- [Research code](https://github.com/matous-volf/political-leaning-prediction).
- Model license: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
- The published trained weights are unchanged. This app adds sentence splitting,
  batching, colors and counts. It does not train or prompt a generative model.
- Model predictions can be wrong, especially on neutral sentences and quotations.
  This is a school-project implementation, not independently verified accuracy.

See [implementation and verification notes](docs/SENTENCE_MODEL.md).

## Run locally

Use Python 3.10+ and Node 20.9+.

```bash
cd backend
bash setup_env.sh
.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
```

The setup downloads the pinned weights into `models/political-leaning`.
The model weights alone are approximately 1.74 GB; allow additional disk and RAM
for PyTorch and inference. This replaces the old `bias_model` default.

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Visit http://localhost:3000. The local frontend uses http://localhost:8000.

## Verify

```bash
backend/.venv/bin/python -m pip install -r requirements-test.txt
backend/.venv/bin/python -m pytest tests/test_sentence_flow.py -q
cd frontend
npm run lint
npm run build
```

## VPS update

The existing site is https://bias.r4him.tech, hosted at `/var/www/biasCheck`.
[Update instructions](docs/SENTENCE_MODEL.md#updating-the-vps) include the required
model-directory change. Deploy the backend and frontend together.
