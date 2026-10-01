"""Prepare Baly data using explicit publisher-domain and exact-text separation.

Reserve the published test first, then validation, then training. Raw article
text remains local. Manifests contain IDs and hashes only. Near-duplicate/event
clustering and time-held-out annotations remain separate research work.
"""
import argparse, csv, hashlib, json, re, subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from tld import get_fld


def normalized_hash(text):
    return hashlib.sha256(re.sub(r'\s+', ' ', text).strip().lower().encode()).hexdigest()


def domain(value):
    host = urlparse(value if '://' in value else 'https://' + value).hostname
    if not host:
        raise ValueError(f'Cannot resolve publisher domain: {value!r}')
    return get_fld('https://' + host.lower(), fail_silently=False)


def prepare(root, output, manifest):
    output.mkdir(parents=True, exist_ok=True)
    seen, reserved, stats, manifests = set(), set(), {}, {}
    all_rows = {}
    for split in ['test', 'valid', 'train']:
        rows, reasons = [], Counter()
        for row in csv.DictReader((root/f'data/splits/media/{split}.tsv').open(), delimiter='\t'):
            item = json.loads((root/'data/jsons'/f"{row['ID']}.json").read_text())
            text = item['content_original'].strip()
            if len(text.split()) < 30:
                reasons['too_short'] += 1
                continue
            key, publisher = normalized_hash(text), domain(item['source_url'])
            if publisher in reserved:
                reasons['publisher_reserved_for_other_split'] += 1
                continue
            if key in seen:
                reasons['duplicate_text'] += 1
                continue
            seen.add(key)
            label = item['bias_text'].upper()
            if label not in {'LEFT','CENTER','RIGHT'}:
                raise ValueError('Unknown label')
            rows.append({'id':item['ID'], 'text':text, 'label':label, 'source':item['source'],
                         'source_group':publisher, 'date':item.get('date'), 'text_sha256':key})
        groups = {r['source_group'] for r in rows}
        reserved.update(groups)
        stats[split] = {'n':len(rows),'excluded':dict(reasons),'labels':dict(Counter(r['label'] for r in rows)),
                        'publisher_domains':sorted(groups)}
        manifests[split] = [{k:v for k,v in r.items() if k!='text'} for r in rows]
        with (output/f'{split}.jsonl').open('w') as f:
            for row in rows: f.write(json.dumps(row)+'\n')
        all_rows[split] = rows
    commit = subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    manifest.write_text(json.dumps({'dataset':'https://github.com/ramybaly/Article-Bias-Prediction',
        'revision':commit,'procedure':'test then valid then train; disjoint registrable publisher domain and normalized exact text',
        'limitations':['Near-duplicate and story leakage not fully audited','Training overlap with existing checkpoints unknown'],
        'splits':stats,'record_manifest_sha256':{k:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for k,v in manifests.items()}},indent=2))
    print(json.dumps(stats,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repository',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);a=p.parse_args();prepare(a.repository,a.output,a.manifest)
