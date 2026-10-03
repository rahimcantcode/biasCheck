"""Offline token-count guard simulation; never changes production decisions."""
import argparse
import hashlib
import json
from pathlib import Path
from repetition_diagnostic import distinct_context,repetition_context


def run(data, probe, audit, tokenizer_dir, output, periodic=False):
    from transformers import AutoTokenizer
    import transformers
    if output.exists():raise ValueError('Use a new output path')
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_dir,local_files_only=True)
    files=sorted(p for p in tokenizer_dir.iterdir() if p.name in {
        'tokenizer.json','tokenizer_config.json','special_tokens_map.json',
        'vocab.json','merges.txt','spm.model','added_tokens.json'})
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    # Match the production bundle fingerprint, not a single-file checksum.
    tokenizer_hash=hashlib.sha256(''.join(name+digest for name,digest in hashes.items()).encode()).hexdigest()
    browser=json.loads(audit.read_text())
    for case in browser['cases']:
        if case['result']['model']['tokenizer_sha256']!=tokenizer_hash:
            raise ValueError('Tokenizer differs from production')
    def measure(row):
        original=row['text'];context=(repetition_context if periodic else distinct_context)(original)
        raw=len(tokenizer(original,add_special_tokens=False,truncation=False)['input_ids'])
        distinct=len(tokenizer(context,add_special_tokens=False,truncation=False)['input_ids'])
        return {'id':row['id'],'raw_tokens':raw,'distinct_context_tokens':distinct,
                'text_changed':context!=original,'raw_short':raw<12,'candidate_short':min(raw,distinct)<12,
                'text_sha256':hashlib.sha256(original.encode()).hexdigest(),
                'context_sha256':hashlib.sha256(context.encode()).hexdigest()}
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    records=[measure(row) for row in rows]
    probes=[measure(row) for row in json.loads(probe.read_text())]
    actual={c['id']:c['result']['overall'] for c in browser['cases']}
    for row in probes:
        if row['raw_tokens']!=actual[row['id']]['token_count']:raise ValueError('Local token count fails to reproduce live probe')
        row['production_decision']=actual[row['id']]['decision']
        row['production_label']=actual[row['id']]['label']
    report={'purpose':'Research-only shadow minimum-context gate, not classifier accuracy',
        'release_approved':False,'validation_read':False,'reserved_test_read':False,
        'tokenizer_sha256':tokenizer_hash,'tokenizer_files':hashes,'transformers':transformers.__version__,
        'threshold':12,'rule':'min(original tokens, context-view tokens) < 12',
        'context_view':'exact whole-input word cycles, otherwise distinct paragraphs' if periodic else 'distinct paragraphs',
        'records':records,'probes':probes,'n':len(rows),
        'changed_context_n':sum(r['text_changed'] for r in records),
        'new_short_n':sum(r['candidate_short'] and not r['raw_short'] for r in records),
        'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (data,probe,audit)},
        'cautions':['Does not change model input, scores or deployed policy',
                    'Exact patterns only, not general semantic novelty detection',
                    'Training corpus audit cannot validate human coverage or legitimate repetition',
                    'Candidate built after observing the probe failure, not independent validation']}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('n','changed_context_n','new_short_n','probes')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('data','probe','audit','tokenizer_dir','output'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    parser.add_argument('--periodic',action='store_true')
    args=parser.parse_args();run(args.data,args.probe,args.audit,args.tokenizer_dir,args.output,args.periodic)
