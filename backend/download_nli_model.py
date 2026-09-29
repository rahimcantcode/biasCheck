"""Download and verify the pinned experimental checkpoint. Run from any directory."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'research/checkpoints/political-debate-large')
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name('nli_checkpoint.json').read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for name, expected in manifest['files'].items():
        destination = args.output / name
        if destination.exists() and sha256(destination) == expected:
            print(f'Already verified: {name}', flush=True)
            continue
        url = f"https://huggingface.co/{manifest['model_id']}/resolve/{manifest['revision']}/{name}"
        temporary = destination.with_suffix(destination.suffix + '.part')
        print(f'Downloading {name}', flush=True)
        with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
            while block := response.read(8 * 1024 * 1024):
                output.write(block)
        if sha256(temporary) != expected:
            temporary.unlink()
            raise RuntimeError(f'Checksum mismatch: {name}')
        temporary.replace(destination)
    print(f'Checkpoint ready: {args.output.resolve()}')


if __name__ == '__main__':
    main()
