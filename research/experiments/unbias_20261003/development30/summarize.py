"""Descriptive synthetic development metrics, never held-out accuracy."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('results',type=Path);a=p.parse_args()
fixture=json.loads(Path(__file__).with_name('cases.json').read_text())
report=json.loads(a.results.read_text());byid={r['id']:r for r in report['rows']}
rows=[]
for c in fixture['cases']:
    r=byid.get(c['id'],{});spans=r.get('response',{}).get('spans',[]);expected=c['expected_spans']
    exact=sum(any(s['start']==e['start'] and s['end']==e['end'] for s in spans) for e in expected)
    overlap=sum(any(s['start']<e['end'] and e['start']<s['end'] for s in spans) for e in expected)
    extra=sum(not any(s['start']<e['end'] and e['start']<s['end'] for e in expected) for s in spans)
    rows.append(dict(id=c['id'],category=c['category'],completed='response' in r,status=r.get('response',{}).get('status','failed_or_missing'),expected=len(expected),predicted=len(spans),exact_expected_matches=exact,overlapped_expected=overlap,nonoverlapping_predictions=extra,seconds=r.get('seconds'),highlights=[s['text'] for s in spans]))
neg=[r for r in rows if r['expected']==0 and r['completed']]
summary=dict(caveat='AI-authored short synthetic development passages and expectations; descriptive task-alignment results only. Overlap is not semantic correctness. Failed cases remain in rows. No baseline comparison or independent human evaluation.',total=len(rows),completed=sum(r['completed'] for r in rows),expected_spans=sum(r['expected'] for r in rows),predicted_spans=sum(r['predicted'] for r in rows),exact_expected_matches=sum(r['exact_expected_matches'] for r in rows),overlapped_expected=sum(r['overlapped_expected'] for r in rows),nonoverlapping_predictions=sum(r['nonoverlapping_predictions'] for r in rows),negative_controls_completed=len(neg),negative_controls_with_highlights=sum(r['predicted']>0 for r in neg),median_seconds=statistics.median(r['seconds'] for r in rows if r['seconds'] is not None),rows=rows)
print(json.dumps(summary,indent=2))
