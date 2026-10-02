"""Compare two independent pilot reviews. Does not manufacture final gold labels."""
import argparse,json
from collections import Counter
from datetime import datetime
from pathlib import Path
import unicodedata
LABELS={'LEFT','CENTER','RIGHT','NONPOLITICAL','UNCERTAIN'}

def reviewer_key(value):
    if not isinstance(value,str) or not value.strip():
        raise ValueError('Reviewer identity is required')
    return unicodedata.normalize('NFKC',value).strip().casefold()

def validate_timestamp(value):
    if not isinstance(value,str) or 'T' not in value:
        raise ValueError('Completion timestamp must be a timezone-aware ISO datetime')
    try:
        parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid completion timestamp') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError('Completion timestamp requires an explicit timezone')

def validate(review,manifest):
    if review.get('pilot_id')!=manifest['pilot_id'] or review.get('rubric_version')!='v1':raise ValueError('Pilot or rubric mismatch')
    reviewer=review.get('reviewer_id')
    reviewer_key(reviewer)
    known={r['id']:r for r in manifest['items']};seen=set();result={}
    if len(known)!=len(manifest['items']):raise ValueError('Duplicate manifest item IDs')
    for row in review.get('annotations',[]):
        id=row.get('id')
        if id not in known or id in seen:raise ValueError('Unknown or duplicate item ID')
        seen.add(id)
        if row.get('reviewer_id')!=reviewer:raise ValueError('Inconsistent reviewer identity')
        if row.get('text_sha256')!=known[id]['text_sha256']:raise ValueError('Text snapshot mismatch')
        validate_timestamp(row.get('completed_at'))
        if row.get('status')=='skipped':
            if not row.get('skip_reason','').strip():raise ValueError('Skip reason required')
            continue
        if row.get('status')!='reviewed' or row.get('full_text_read') is not True:raise ValueError('Full-text review required')
        r,l=row.get('relevance'),row.get('label')
        if r not in {'POLITICAL','NONPOLITICAL','UNCERTAIN'} or l not in LABELS:raise ValueError('Invalid relevance or label')
        if (r=='POLITICAL' and l=='NONPOLITICAL') or (r!='POLITICAL' and l!=r):raise ValueError('Inconsistent relevance and label')
        if row.get('confidence') not in {'low','medium','high'} or len(row.get('rationale','').strip())<15 or not row.get('completed_at'):raise ValueError('Missing review evidence')
        result[id]=row
    return result

def agreement(pairs,field):
    if not pairs:return {'n':0,'agreement':None,'cohens_kappa':None}
    n=len(pairs);a=Counter(x[field] for x,y in pairs);b=Counter(y[field] for x,y in pairs)
    observed=sum(x[field]==y[field] for x,y in pairs)/n;chance=sum(a[k]*b[k] for k in set(a)|set(b))/n**2
    return {'n':n,'agreement':observed,'cohens_kappa':(observed-chance)/(1-chance) if chance<1 else None}

def compare(first,second,manifest):
    if reviewer_key(first.get('reviewer_id'))==reviewer_key(second.get('reviewer_id')):raise ValueError('Two distinct independent reviewers required')
    a,b=validate(first,manifest),validate(second,manifest);common=sorted(set(a)&set(b));pairs=[(a[k],b[k]) for k in common];items={r['id']:r for r in manifest['items']}
    disagreements=[{'id':k,'reviewer_a':a[k],'reviewer_b':b[k],'adjudicated_label':None,'adjudicated_relevance':None,'adjudicator_id':None,'adjudication_rationale':None} for k in common if any(a[k][f]!=b[k][f] for f in ['label','relevance'])]
    return {'pilot_id':manifest['pilot_id'],'purpose':'rubric development only','reviewers':[first['reviewer_id'],second['reviewer_id']],
       'completed':[len(a),len(b)],'paired_n':len(common),'missing_or_skipped_ids':sorted(set(items)-set(common)),
       'label_agreement':agreement(pairs,'label'),'relevance_agreement':agreement(pairs,'relevance'),
       'slices':{kind:agreement([(a[k],b[k]) for k in common if items[k]['kind']==kind],'label') for kind in ['historical_article','controlled_example']},
       'disagreements':disagreements,'gold_labels_approved':False,'limitations':['Reviewer independence requires human confirmation','Agreement is not accuracy','Consensus is not automatically a gold label','Pilot examples cannot become an independent final test']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--first',type=Path,required=True);p.add_argument('--second',type=Path,required=True);p.add_argument('--manifest',type=Path,default=Path(__file__).with_name('pilot_manifest.json'));p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=compare(json.loads(a.first.read_text()),json.loads(a.second.read_text()),json.loads(a.manifest.read_text()))
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['disagreements','missing_or_skipped_ids']},indent=2))
