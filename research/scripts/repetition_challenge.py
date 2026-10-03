"""Synthetic formatting probes for the offline guard; no political gold labels."""
import argparse
import hashlib
import json
from pathlib import Path
from repetition_diagnostic import distinct_context


def cases(title,body):
    return [
        ('single','base',title),
        ('blank-lines','exact-paragraph','\n\n'.join([title]*8)),
        ('crlf','exact-paragraph','\r\n\r\n'.join([title]*8)),
        ('spaces-in-paragraphs','exact-paragraph','\n\n'.join([title,'  '.join(title.split())]*4)),
        ('single-newlines','known-gap','\n'.join([title]*8)),
        ('spaces-only','known-gap',' '.join([title]*8)),
        ('numbered','known-gap','\n\n'.join(str(i+1)+'. '+title for i in range(8))),
        ('punctuation','known-gap','\n\n'.join(title+'.'*i for i in range(8))),
        ('body-control','additional-context',body),
        ('repeat-plus-body','additional-context','\n\n'.join([title]*8+[body])),
    ]


def run(data,tokenizer_dir,prior,output):
    from transformers import AutoTokenizer
    if output.exists():raise ValueError('Use a new output directory')
    tokenizer=AutoTokenizer.from_pretrained(tokenizer_dir,local_files_only=True)
    previous=json.loads(prior.read_text())
    for name,digest in previous['tokenizer_files'].items():
        if hashlib.sha256((tokenizer_dir/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Tokenizer file changed')
    source=json.loads(data.read_text().splitlines()[0])
    title,body=source['text'].split('\n\n',1)
    records=[]
    for id,kind,text in cases(title,body):
        context=distinct_context(text)
        raw=len(tokenizer(text,add_special_tokens=False,truncation=False)['input_ids'])
        distinct=len(tokenizer(context,add_special_tokens=False,truncation=False)['input_ids'])
        records.append({'id':id,'kind':kind,'text':text,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'raw_tokens':raw,'distinct_tokens':distinct,'candidate_short':min(raw,distinct)<12})
    report={'purpose':'AI-constructed development formatting challenge; no human political labels',
        'release_approved':False,'reserved_test_read':False,'validation_read':False,
        'source_training_id':source['id'],'tokenizer_sha256':previous['tokenizer_sha256'],
        'input_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
        'prior_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),
        'threshold':12,'records':[{k:v for k,v in r.items() if k!='text'} for r in records],
        'cautions':['Post hoc development cases, not independent evaluation',
                    'Additional context is not a human judgment of sufficiency or relevance',
                    'No accuracy, general bypass rate or false-positive estimate is claimed']}
    output.mkdir(parents=True)
    (output/'results.json').write_text(json.dumps(report,indent=2))
    (output/'cases.json').write_text(json.dumps(records,indent=2))
    (output/'browser.json').write_text(json.dumps([{k:r[k] for k in ('id','text')} for r in records if r['id'] in ('single-newlines','spaces-only','repeat-plus-body')],indent=2))
    print(json.dumps(report['records'],indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('data','tokenizer_dir','prior','output'):parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=parser.parse_args();run(a.data,a.tokenizer_dir,a.prior,a.output)
