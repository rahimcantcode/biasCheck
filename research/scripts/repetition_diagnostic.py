"""Exact paragraph repetition telemetry, not a semantic-context or release gate."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def distinct_context(text):
    """Research-only context view; unchanged text when no duplicates exist."""
    seen=set();kept=[];duplicate=False
    for paragraph in re.split(r'\r?\n\s*\r?\n',text):
        key=' '.join(paragraph.split())
        if key and key in seen:
            duplicate=True
            continue
        seen.add(key);kept.append(paragraph)
    return '\n\n'.join(kept) if duplicate else text


def diagnose(text):
    paragraphs=[' '.join(p.split()) for p in re.split(r'\r?\n\s*\r?\n',text) if p.strip()]
    unique=list(dict.fromkeys(paragraphs))
    words=sum(len(p.split()) for p in paragraphs)
    unique_words=sum(len(p.split()) for p in unique)
    return {'paragraph_n':len(paragraphs),'distinct_paragraph_n':len(unique),
            'duplicate_paragraph_n':len(paragraphs)-len(unique),
            'word_count':words,'distinct_paragraph_word_count':unique_words,
            'retained_word_fraction':unique_words/words if words else None,
            'normalization':'Whitespace collapsed within paragraphs; case and punctuation preserved',
            'text_sha256':hashlib.sha256(text.encode()).hexdigest()}


def run(data, output):
    if output.exists():raise ValueError('Use a new output path')
    rows=[json.loads(line) for line in data.read_text().splitlines()]
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate IDs')
    records=[{'id':r['id'],**diagnose(r['text'])} for r in rows]
    report={'purpose':'Training-only exact paragraph repetition audit, not semantic sufficiency',
            'input_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
            'reserved_test_read':False,'release_approved':False,
            'n':len(records),'with_duplicate_paragraphs':sum(r['duplicate_paragraph_n']>0 for r in records),
            'records':records,
            'cautions':['Word counts are not tokenizer counts',
                        'Exact matching misses paraphrase and same-paragraph repetition',
                        'Legitimate quotations or refrains may repeat; no decision policy or threshold proposed',
                        'Distinct paragraphs do not prove new information or political relevance']}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('n','with_duplicate_paragraphs')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.data,args.output)
