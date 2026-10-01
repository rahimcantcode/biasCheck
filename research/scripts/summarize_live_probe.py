"""Summarize observed deployment behavior without inventing accuracy or labels."""
import argparse,json,statistics
from pathlib import Path


def summarize(path,output):
    report=json.loads(path.read_text())
    if 'attempted_n' not in report:raise ValueError('Probe is still running; wait for the final checkpoint')
    successful=[x for x in report['predictions'] if 'response' in x];lookup={x['case_id']:x for x in successful}
    def prediction(row):
        body=row['response'];return body.get('overall') or body['results'][0]
    lines=['# Deployed controlled-input diagnostics','',
      'This is an unlabeled synthetic stress test, not a measurement of real-world accuracy.',
      'The review page does not load this report. Reviewers should avoid these predictions until their independent judgments are submitted.','',
      f"Run started: {report['started_at']}",f"Endpoint: {report['endpoint']}",
      f"Completed responses: {len(successful)} / {report['attempted_n']} attempted.",
      f"Observed label counts: {report['observed_label_counts']}",
      f"Top raw score at least .95: {report['top_score_at_least_095_n']} successful responses.",
      f"Median observed request duration: {statistics.median(x['seconds'] for x in successful):.2f} seconds." if successful else 'No successful responses.',
      '', 'The legacy health endpoint does not identify the checkpoint or runtime. Request durations include network and server time; they are not a controlled latency benchmark.','',
      '| Controlled case | Returned label | Top raw score |','|---|---|---|']
    cases={'S01':'Dinner description','S10':'Conservative repair estimate','S11':'Liberal amount of glue','S12':'Left/right door directions','S17':'Public healthcare and progressive taxation','S18':'Lower taxes and deregulation','S23':'Attributed higher-tax quotation','S24':'Attributed lower-tax quotation','S31':'Single word: Taxes','S33':'Transparency criticism, Democratic mayor','S34':'Transparency criticism, Republican mayor'}
    for key,name in cases.items():
        if key in lookup:
            p=prediction(lookup[key]);scores=p.get('probabilities',{});score=max(scores.values()) if scores else float('nan');lines.append(f"| {name} | {p.get('label')} | {score:.6f} |")
    lines+=['','## Interpretation limits','',
      '- Directional labels on clearly ordinary nonpolitical inputs demonstrate an intended-use failure, but this convenience sample cannot estimate the population false-positive rate.',
      '- A very high raw score does not establish correctness or political relevance. Merely raising the confidence threshold can retain such failures.',
      '- Historical deployment parity on a few inputs is not proof that the same checkpoint is still deployed; health provenance is missing.',
      '- No human annotations, calibrated probabilities, final accuracy, or retraining results are produced by this script.',
      '- Next model-development priority remains a validated relevance/insufficient-context stage followed by ideological classification, evaluated separately on human-reviewed data.']
    output.write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();summarize(a.input,a.output)
