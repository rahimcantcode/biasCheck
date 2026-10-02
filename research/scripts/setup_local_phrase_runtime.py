"""Fetch only pinned public inference artifacts, verify bytes, extract safely.

No credentials, package installation, public listener, model execution, or paid
service. Files stay in the explicitly chosen directory (default git-ignored).
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST=ROOT/'research/local_phrase_runtime.json'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(8*1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def fetch_verified(url,path,expected_sha,expected_size=None):
    if not url.startswith('https://'):raise ValueError('Only pinned HTTPS artifacts supported')
    if path.exists():
        if digest(path)!=expected_sha or (expected_size is not None and path.stat().st_size!=expected_size):raise ValueError(f'Existing artifact mismatch: {path.name}')
        return
    path.parent.mkdir(parents=True,exist_ok=True)
    partial=path.with_name(path.name+'.partial')
    if partial.exists():raise ValueError('Partial artifact exists; inspect it before a new download')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    count=0
    try:
        with opener.open(url,timeout=120) as response,partial.open('xb') as out:
            for chunk in iter(lambda:response.read(1024*1024),b''):
                count+=len(chunk)
                if expected_size is not None and count>expected_size:raise ValueError('Artifact exceeds pinned byte size')
                out.write(chunk)
        if digest(partial)!=expected_sha or (expected_size is not None and count!=expected_size):raise ValueError('Artifact size/SHA mismatch')
        partial.replace(path)
    except BaseException:
        # Preserve partial bytes for inspection; never mistake them for a model.
        raise


def extract_runtime(archive,destination):
    if destination.exists():raise ValueError('Refusing to overwrite runtime extraction')
    destination.mkdir(parents=True)
    with tarfile.open(archive,'r:gz') as source:
        source.extractall(destination,filter='data')


def setup(output,model_key,manifest_path=DEFAULT_MANIFEST):
    raw=manifest_path.read_bytes();manifest=json.loads(raw)
    if manifest.get('schema_version')!=1 or model_key not in manifest['models']:raise ValueError('Unknown pinned model')
    runtime=manifest['runtime'];model=manifest['models'][model_key]
    output.mkdir(parents=True,exist_ok=True)
    archive=output/Path(runtime['asset_url']).name
    fetch_verified(runtime['asset_url'],archive,runtime['asset_digest'].removeprefix('sha256:'),runtime['asset_bytes'])
    extracted=output/'runtime'
    if not extracted.exists():extract_runtime(archive,extracted)
    server=extracted/runtime['server_relative_path']
    if not server.is_file() or digest(server)!=runtime['server_sha256']:raise ValueError('Runtime executable differs from pinned build')
    weights=output/'models'/model['file']
    fetch_verified(model['weights_url'],weights,model['sha256'],model['bytes'])
    # License reference is retained; acceptance/production rights review is not automated.
    record={'manifest_sha256':hashlib.sha256(raw).hexdigest(),'runtime':runtime,'model_key':model_key,'model':model,
            'server':str(server.resolve()),'weights':str(weights.resolve()),'release_approved':False}
    (output/(model_key+'.installed.json')).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'status':'verified','server':str(server),'weights':str(weights),'release_approved':False}))
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'research/checkpoints/local-phrase-runtime');p.add_argument('--model',required=True);p.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST);a=p.parse_args()
    setup(a.output.resolve(),a.model,a.manifest.resolve())
