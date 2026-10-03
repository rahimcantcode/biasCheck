"""Research-only original-text adapters. No ideology or speaker inference."""
from __future__ import annotations
import hashlib

BIAS_TYPES = {'dehumanizing_language','stereotypical_association','sensationalism',
'opinion_as_fact','unsupported_generalization','euphemism','informational_bias','loaded_language'}


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def exact_offsets(text, phrase):
    if not isinstance(phrase, str) or not phrase:
        raise ValueError('empty_or_invalid_phrase')
    starts=[]
    pos=text.find(phrase)
    while pos >= 0:
        starts.append(pos)
        pos=text.find(phrase,pos+1)
    if len(starts)!=1:
        raise ValueError('unmatched_phrase' if not starts else 'ambiguous_occurrence')
    return starts[0], starts[0]+len(phrase)


def adapt_unbias_v2(text, result):
    """Require native schema and exact unique spans; never use cleaned offsets.

    Unknown attribution is intentional: the native model has no speaker output.
    A rejected segment remains a partial failure, never an empty success.
    """
    if not isinstance(result,dict) or set(result)!={'severity','biased_segments','unbiased_text'}:
        raise ValueError('invalid_native_schema')
    severity=result['severity']; segments=result['biased_segments']
    if type(severity) is not int or not 0<=severity<=10 or not isinstance(segments,list):
        raise ValueError('invalid_severity_or_segments')
    if len(segments)>64 or not isinstance(result['unbiased_text'],str):
        raise ValueError('invalid_native_schema')
    if (severity==0)!= (len(segments)==0):
        raise ValueError('inconsistent_severity')
    spans=[]; rejected=[]
    for i,segment in enumerate(segments):
        try:
            if not isinstance(segment,dict) or set(segment)!={'original','replacement','severity','bias_type','reasoning'}:
                raise ValueError('invalid_segment_schema')
            if (not isinstance(segment['severity'],str) or not isinstance(segment['bias_type'],str)
                    or segment['severity'] not in {'Low','Medium','High'} or segment['bias_type'] not in BIAS_TYPES):
                raise ValueError('invalid_segment_labels')
            if any(not isinstance(segment[k],str) for k in ('replacement','reasoning')):
                raise ValueError('invalid_segment_text')
            start,end=exact_offsets(text,segment['original'])
            spans.append({'text':text[start:end],'start':start,'end':end,'attribution':'unknown',
                          'reason':segment['reasoning'],'bias_type':segment['bias_type'],'native_index':i})
        except ValueError as exc:
            rejected.append({'native_index':i,'reason':str(exc)})
    # Reject both sides of every conflict instead of arbitrarily keeping the first.
    conflict={s['native_index'] for s in spans for t in spans
              if s is not t and s['start']<t['end'] and t['start']<s['end']}
    rejected.extend({'native_index':i,'reason':'overlap_or_duplicate'} for i in sorted(conflict))
    spans=[s for s in spans if s['native_index'] not in conflict]
    status='partial_failure' if rejected else ('suggestions' if spans else 'no_suggestions')
    return {'status':status,'source_sha256':sha(text),'spans':spans,'rejected':rejected,
            'attribution_supported':False,'offset_unit':'unicode_codepoint','end_exclusive':True}


def decode_bio(text, offsets, labels):
    """Decode token labels via raw-source offsets, excluding special tokens.

    Orphan I labels start a span and are counted explicitly. All attribution is
    unknown; no probability is represented as correctness confidence.
    """
    if len(offsets)!=len(labels):raise ValueError('length_mismatch')
    spans=[];active=None;orphans=0;last_end=0
    for (start,end),label in zip(offsets,labels):
        if label not in {'O','B-BIAS','I-BIAS'}:raise ValueError('invalid_bio_label')
        if type(start) is not int or type(end) is not int:raise ValueError('invalid_token_offsets')
        if (start,end)==(0,0):
            if active:spans.append(active);active=None
            continue
        if not (type(start) is int and type(end) is int and last_end<=start<end<=len(text)):
            raise ValueError('invalid_token_offsets')
        last_end=end
        if label=='O':
            if active:spans.append(active);active=None
            continue
        if label=='B-BIAS' or active is None:
            if active:spans.append(active)
            if label=='I-BIAS':orphans+=1
            active={'start':start,'end':end}
        else:
            active['end']=end
    if active:spans.append(active)
    for span in spans:
        span.update(text=text[span['start']:span['end']],attribution='unknown')
    return {'status':'suggestions' if spans else 'no_suggestions','spans':spans,
            'source_sha256':sha(text),'orphan_i_count':orphans,'attribution_supported':False,
            'offset_unit':'unicode_codepoint','end_exclusive':True}


def span_metrics(expected,predicted):
    """Exact source-bound spans. No attribution or semantic overlap credit."""
    gold={(x['start'],x['end']) for x in expected}
    pred={(x['start'],x['end']) for x in predicted}
    return {'true_positive':len(gold&pred),'false_positive':len(pred-gold),'false_negative':len(gold-pred)}
