"""Hash-verified unlabeled pilot audit; no inherited publisher labels."""
import argparse
import hashlib
import json
from pathlib import Path
import requests
from repetition_diagnostic import repetition_context


def verified_text(item,text):
    if hashlib.sha256(text.encode()).hexdigest()!=item['text_sha256']:
        raise ValueError('Frozen text hash mismatch: '+item['id'])
    return text


def run(manifest,tokenizer_dir,prior,output):
    from transformers import AutoTokenizer
    if output.exists():raise ValueError('Use a new output directory')
    pilot=json.loads(manifest.read_text())
    if len({r['id'] for r in pilot['items']})!=len(pilot['items']):raise ValueError('Duplicate pilot IDs')
    reference=json.loads(prior.read_text())
    for name,digest in reference['tokenizer_files'].items():
        if hashlib.sha256((tokenizer_dir/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Tokenizer file mismatch')
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_dir,local_files_only=True)
    output.mkdir(parents=True)
    report={'purpose':'Unlabeled rubric-development pilot context audit, not independent accuracy',
        'human_reviewed':False,'release_approved':False,'reserved_test_read':False,
        'pilot_id':pilot['pilot_id'],'dataset_revision':pilot['dataset_revision'],
        'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
        'tokenizer_sha256':reference['tokenizer_sha256'],'threshold':12,'records':[]}
    texts=[]
    with requests.Session() as session:
        for item in pilot['items']:
            record={'id':item['id'],'kind':item['kind'],'text_sha256':item['text_sha256']}
            try:
                text=item['text']
                if item['kind']=='historical_article':
                    url='https://raw.githubusercontent.com/ramybaly/Article-Bias-Prediction/'+pilot['dataset_revision']+'/data/jsons/'+str(item['dataset_id'])+'.json'
                    response=session.get(url,timeout=30);response.raise_for_status()
                    text=response.json()['content_original'].strip()
                    record['source_url']=url
                text=verified_text(item,text)
                context=repetition_context(text)
                raw=len(tokenizer(text,add_special_tokens=False,truncation=False,verbose=False)['input_ids'])
                distinct=len(tokenizer(context,add_special_tokens=False,truncation=False,verbose=False)['input_ids'])
                record.update(raw_tokens=raw,context_tokens=distinct,context_changed=context!=text,
                    raw_short=raw<12,candidate_short=min(raw,distinct)<12,status='verified')
                texts.append({'id':item['id'],'text':text})
            except (requests.RequestException,ValueError,KeyError,TypeError) as exc:
                record.update(status='failed',error=str(exc))
            report['records'].append(record)
            (output/'results.json').write_text(json.dumps(report,indent=2))
            print(item['id'],record['status'],flush=True)
    report['summary']={}
    for kind in ('historical_article','controlled_example'):
        selected=[r for r in report['records'] if r['kind']==kind]
        good=[r for r in selected if r['status']=='verified']
        report['summary'][kind]={'requested':len(selected),'verified':len(good),'failed':len(selected)-len(good),
            'context_changed':sum(r['context_changed'] for r in good),
            'new_short':sum(r['candidate_short'] and not r['raw_short'] for r in good),
            'already_short':sum(r['raw_short'] for r in good)}
    report['cautions']=['No human sufficiency, relevance or political labels supplied',
        'Previously prepared development pilot, not independent final test',
        'Inherited dataset bias labels not used; reuse rights need review before redistribution',
        'Zero gate changes would not establish a false-positive rate or robustness guarantee']
    (output/'results.json').write_text(json.dumps(report,indent=2))
    (output/'texts.json').write_text(json.dumps(texts,indent=2))
    # Ordered first three verified historical articles; no class-label selection.
    allowed={r['id'] for r in report['records'] if r['kind']=='historical_article' and r['status']=='verified'}
    (output/'browser.json').write_text(json.dumps([r for r in texts if r['id'] in allowed][:3],indent=2))
    print(json.dumps(report['summary'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('manifest','tokenizer_dir','prior','output'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=parser.parse_args();run(a.manifest,a.tokenizer_dir,a.prior,a.output)
