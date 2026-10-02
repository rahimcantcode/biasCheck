"""Full-document evaluation; raw accuracy is distinct from accepted-label accuracy."""
import argparse, hashlib, json, math, os, sys, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report


def wilson_interval(successes, n):
    """Marginal 95% binomial diagnostic only; ignores event/source dependence."""
    if not n:
        return None
    z=1.959963984540054;p=successes/n;den=1+z*z/n
    middle=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,middle-half),min(1.,middle+half)]


def summarize(rows):
    """Describe the supplied evaluation mix, never assumed production traffic.

    UNCERTAIN references are not reliable negative gold. Exact reference match
    across all accepted rows is therefore separate from reference match on accepted
    non-UNCERTAIN references, and uncertain acceptance is reported on its own.
    """
    labels = ['LEFT', 'CENTER', 'RIGHT']
    references = labels + ['NONPOLITICAL', 'UNCERTAIN']
    predictions = labels + ['ABSTAIN']
    for row in rows:
        if row['gold'] not in references:
            raise ValueError('Unknown reference label')
        if row['raw_label'] not in labels or row['decision'] not in ['classified', 'abstained']:
            raise ValueError('Invalid model output')
        if ((row['decision'] == 'classified' and row['label'] not in labels)
                or (row['decision'] == 'abstained' and row['label'] is not None)):
            raise ValueError('Inconsistent decision and label')

    political = [r for r in rows if r['gold'] in labels]
    political_accepted = [r for r in political if r['decision'] == 'classified']
    accepted = [r for r in rows if r['decision'] == 'classified']
    non_uncertain_accepted = [r for r in accepted if r['gold'] != 'UNCERTAIN']
    nonpolitical = [r for r in rows if r['gold'] == 'NONPOLITICAL']
    uncertain = [r for r in rows if r['gold'] == 'UNCERTAIN']
    # Accepted outputs are political labels, so only political references can match.
    correct = sum(r['label'] == r['gold'] for r in accepted)
    nonpolitical_accepted_n = sum(r['decision'] == 'classified' for r in nonpolitical)
    uncertain_accepted_n = sum(r['decision'] == 'classified' for r in uncertain)

    def rate(numerator, denominator):
        return numerator / denominator if denominator else None

    matrix = [[0 for _ in predictions] for _ in references]
    for row in rows:
        prediction = row['label'] if row['decision'] == 'classified' else 'ABSTAIN'
        matrix[references.index(row['gold'])][predictions.index(prediction)] += 1

    report = {
        'n': len(rows),
        'political_n': len(political),
        'political_accepted_n': len(political_accepted),
        'abstained_political_n': len(political) - len(political_accepted),
        'political_correct_accepted_n': correct,
        'political_selective_accuracy': rate(correct, len(political_accepted)),
        'political_coverage': rate(len(political_accepted), len(political)),
        'all_accepted_n': len(accepted),
        'all_input_coverage': rate(len(accepted), len(rows)),
        'all_accepted_reference_match_n': correct,
        'all_accepted_reference_match': rate(correct, len(accepted)),
        'non_uncertain_accepted_n': len(non_uncertain_accepted),
        'non_uncertain_accepted_reference_match_n': correct,
        'accepted_reference_match_excluding_uncertain': rate(correct, len(non_uncertain_accepted)),
        'nonpolitical_n': len(nonpolitical),
        'nonpolitical_accepted_n': nonpolitical_accepted_n,
        'nonpolitical_false_label_rate': rate(nonpolitical_accepted_n, len(nonpolitical)),
        'uncertain_n': len(uncertain),
        'uncertain_accepted_n': uncertain_accepted_n,
        'uncertain_acceptance_rate': rate(uncertain_accepted_n, len(uncertain)),
        'full_population_decision_confusion_rows': references,
        'full_population_decision_confusion_columns': predictions,
        'full_population_decision_confusion_matrix': matrix,
        # Keep the v2 political-only matrix available to existing consumers.
        'decision_confusion_rows': labels,
        'decision_confusion_columns': predictions,
        'decision_confusion_matrix': matrix[:3],
        'political_macro_f1': None,
        'political_per_class': {},
        'metrics_schema': 'v3: explicit political-only and full-population denominators; v2 aliases retained',
        'metric_definitions': {
            'political_selective_accuracy': 'Correct accepted political references / political_accepted_n',
            'political_coverage': 'political_accepted_n / political_n',
            'all_input_coverage': (
                'all_accepted_n / n; classified-label coverage, not processed-response coverage; '
                'valid abstentions do not count as accepted labels'),
            'all_accepted_reference_match': (
                'Exact accepted label/reference matches / all_accepted_n, including NONPOLITICAL and '
                'UNCERTAIN; UNCERTAIN nonmatches are not established classification errors'),
            'accepted_reference_match_excluding_uncertain': (
                'Exact accepted label/reference matches / non_uncertain_accepted_n; denominator includes accepted '
                'LEFT/CENTER/RIGHT/NONPOLITICAL references and excludes all UNCERTAIN references; '
                'exclusion does not establish remaining reference validity'),
            'uncertain_acceptance_rate': (
                'uncertain_accepted_n / uncertain_n; acceptance frequency, not a false-label rate '
                'against reliable negative gold'),
            'raw_and_decision_class_metrics': (
                'raw_*, macro_f1, per_class, per_class_coverage and decision_confusion_* '
                'use LEFT/CENTER/RIGHT reference rows only'),
        },
        'limitations': [
            'Metrics describe the supplied evaluation mix and do not establish representative traffic performance',
            'Accepted-reference-match and coverage rates depend on the evaluation mix',
            'UNCERTAIN references are not reliable negative gold; inspect uncertain acceptance separately',
        ],
    }
    aliases = {
        'eligible_n': 'political_n',
        'accepted_n': 'political_accepted_n',
        'coverage': 'political_coverage',
        'selective_accuracy': 'political_selective_accuracy',
        # Historical name retained for readers of v2 reports; not an error rate.
        'uncertain_false_label_rate': 'uncertain_acceptance_rate',
    }
    report['metric_aliases'] = aliases
    report.update({alias: report[target] for alias, target in aliases.items()})
    diagnostics = {
        'method': 'Wilson 95%; illustrative only, ignores source/episode dependence and repeated model selection',
        'political_selective_accuracy': wilson_interval(correct, len(political_accepted)),
        'political_coverage': wilson_interval(len(political_accepted), len(political)),
        'all_input_coverage': wilson_interval(len(accepted), len(rows)),
        'all_accepted_reference_match': wilson_interval(correct, len(accepted)),
        'accepted_reference_match_excluding_uncertain': wilson_interval(correct, len(non_uncertain_accepted)),
        'nonpolitical_false_label_rate': wilson_interval(nonpolitical_accepted_n, len(nonpolitical)),
        'uncertain_acceptance_rate': wilson_interval(uncertain_accepted_n, len(uncertain)),
    }
    diagnostics.update({alias: diagnostics[target] for alias, target in aliases.items() if target in diagnostics})
    report['marginal_binomial_diagnostics'] = diagnostics
    if political:
        y = [r['gold'] for r in political]
        p = [r['raw_label'] for r in political]
        decisions = [r['label'] if r['decision'] == 'classified' else 'ABSTAIN' for r in political]
        product_f1 = f1_score(y, decisions, labels=labels, average='macro', zero_division=0)
        product_per_class = classification_report(y, decisions, labels=labels, output_dict=True, zero_division=0)
        report.update(
            raw_accuracy=accuracy_score(y, p),
            raw_macro_f1=f1_score(y, p, labels=labels, average='macro', zero_division=0),
            raw_per_class=classification_report(y, p, labels=labels, output_dict=True, zero_division=0),
            macro_f1=product_f1,
            political_macro_f1=product_f1,
            raw_confusion_order=labels,
            raw_confusion_matrix=confusion_matrix(y, p, labels=labels).tolist(),
            per_class=product_per_class,
            political_per_class=product_per_class,
            per_class_coverage={
                label: rate(sum(r['decision'] == 'classified' for r in political if r['gold'] == label),
                            sum(r['gold'] == label for r in political))
                for label in labels},
        )
    return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--model',type=Path,required=True);p.add_argument('--split',choices=['validation','test','stress'],required=True);p.add_argument('--mode',choices=['article','sentence','paragraph'],default='article');p.add_argument('--annotation-record',type=Path,help='Actual annotation provenance JSON, not model-generated labels.');a=p.parse_args()
    os.environ['BIASCHECK_MODEL_DIR']=str(a.model.resolve())
    from backend.model import predict_text,model_metadata
    rows=[json.loads(line) for line in a.input.read_text().splitlines() if line.strip()]
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate IDs')
    results=[];started=time.monotonic()
    for i,row in enumerate(rows):
        output=predict_text(row['text'],a.mode)
        results.append({'id':row['id'],'gold':row['label'],'source':row.get('source','unknown'),
            'source_group':row.get('source_group','unknown'),'text_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),**output})
        if (i+1)%10==0:print('evaluated',i+1,flush=True)
    report={'schema_version':3,'split':a.split,'mode':a.mode,'data_sha256':hashlib.sha256(a.input.read_bytes()).hexdigest(),
        'annotation_provenance':json.loads(a.annotation_record.read_text()) if a.annotation_record else None,
        'model':model_metadata(),'metrics':summarize(results),'seconds':time.monotonic()-started,'predictions':results}
    a.output.write_text(json.dumps(report,indent=2));print(json.dumps(report['metrics'],indent=2))
if __name__=='__main__':main()
