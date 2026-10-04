"""Download the existing trained classifier, without retraining or pickle files."""
import json
from pathlib import Path
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

try:
    from .config import get_settings
except ImportError:
    from config import get_settings


def main():
    checkpoint = json.loads(Path(__file__).with_name('political_checkpoint.json').read_text())
    destination = get_settings().model_dir
    snapshot_download(
        repo_id=checkpoint['model_id'], revision=checkpoint['revision'],
        local_dir=str(destination),
        allow_patterns=['config.json', 'model.safetensors', 'README.md'],
    )
    tokenizer = AutoTokenizer.from_pretrained(
        checkpoint['tokenizer_id'], revision=checkpoint['tokenizer_revision'],
        use_fast=True, trust_remote_code=False,
    )
    tokenizer.save_pretrained(destination)
    (destination / 'checkpoint.json').write_text(json.dumps(checkpoint, indent=2) + '\n')
    print(f"Downloaded {checkpoint['model_id']} to {destination}")


if __name__ == '__main__':
    main()
