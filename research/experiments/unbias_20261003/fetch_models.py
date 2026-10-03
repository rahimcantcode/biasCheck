"""Download only pinned published files; validate hashes before use.

Large files belong outside the synced workspace. Resuming never trusts partial
bytes without a complete final digest. This does not execute model code.
"""
import argparse,hashlib,json,time,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',choices=['native','ner'],required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    meta=json.loads((HERE/('candidate_model_metadata.json' if a.candidate=='native' else 'ner_model_metadata.json')).read_text())
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True);records=[];started=time.monotonic()
    for item in meta['siblings']:
        name=item['rfilename']
        if name=='.gitattributes' or '/' in name or (a.candidate=='native' and name.endswith('.md')):continue
        url=f"https://huggingface.co/{meta['id']}/resolve/{meta['sha']}/{name}"
        path=out/name;part=out/(name+'.partial');expected=item.get('lfs',{}).get('sha256')
        if path.exists():
            if path.stat().st_size!=item['size']:raise ValueError('Existing file size mismatch')
            if expected and digest(path)!=expected:raise ValueError('Existing file hash mismatch')
        else:
            offset=part.stat().st_size if part.exists() else 0
            req=urllib.request.Request(url,headers={'Range':f'bytes={offset}-'} if offset else {})
            with urllib.request.urlopen(req,timeout=60) as res:
                if offset and res.status==206:
                    if not res.headers.get('Content-Range','').startswith(f'bytes {offset}-'):raise ValueError('Invalid range response')
                else:offset=0
                with part.open('ab' if offset else 'wb') as f:
                    for b in iter(lambda:res.read(8*1024*1024),b''):f.write(b)
            if part.stat().st_size!=item['size']:raise ValueError('Downloaded size mismatch')
            if expected and digest(part)!=expected:raise ValueError('Downloaded hash mismatch')
            part.rename(path)
        if not expected:
            b=path.read_bytes()
            if hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()!=item['blobId']:raise ValueError('Git blob hash mismatch')
        records.append({'file':name,'bytes':item['size'],'sha256':digest(path),'source_url':url})
        print('Verified',name,flush=True)
    marker={'model_id':meta['id'],'model_revision':meta['sha'],'files':records,'elapsed_seconds_this_invocation':time.monotonic()-started}
    (out/'VERIFIED.json').write_text(json.dumps(marker,indent=2)+'\n')
if __name__=='__main__':main()
