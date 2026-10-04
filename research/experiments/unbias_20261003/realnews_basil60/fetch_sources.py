"""Fetch exact public data snapshots for local evaluation, not redistribution."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

from prepare import BASIL_REV, TRAIN_REV, TRAIN_SHA


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    args = parser.parse_args()
    args.data.mkdir(parents=True, exist_ok=False)
    url = f'https://api.github.com/repos/launchnlp/BASIL/tarball/{BASIL_REV}'
    archive = fetch(url)
    archive_sha = hashlib.sha256(archive).hexdigest()
    assert archive_sha == '95c7182970281df7b4524dfc4d48a897619a0779ce7810b7b139254a30b46100'
    # Only data files are written. No source scripts from the remote archive run.
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        for member in bundle.getmembers():
            path = Path(member.name)
            if not member.isfile() or path.suffix != '.json' or len(path.parts) < 3:
                continue
            relative = Path(*path.parts[1:])
            if relative.parts[0] not in {'articles', 'annotations'} or '..' in relative.parts:
                continue
            target = args.data / 'basil' / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.extractfile(member).read())
    (args.data / 'basil_provenance.json').write_text(json.dumps(
        {'revision': BASIL_REV, 'url': url, 'archive_sha256': archive_sha}, indent=2))
    training = fetch(f'https://huggingface.co/datasets/vector-institute/unbias-plus-dataset/resolve/{TRAIN_REV}/data/train_4.json')
    assert hashlib.sha256(training).hexdigest() == TRAIN_SHA
    (args.data / 'train_4.json').write_bytes(training)
    print('Verified BASIL and train_4 snapshots saved.')
