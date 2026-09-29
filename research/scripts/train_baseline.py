"""Simple diagnostic on prepared, domain-disjoint train and validation JSONL."""
import argparse,json,time
from pathlib import Path
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score,f1_score,classification_report
p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
train=[json.loads(x) for x in (a.data/'train.jsonl').read_text().splitlines()];valid=[json.loads(x) for x in (a.data/'valid.jsonl').read_text().splitlines()]
assert not {r['source_group'] for r in train}&{r['source_group'] for r in valid}
assert not {r['text_sha256'] for r in train}&{r['text_sha256'] for r in valid}
start=time.monotonic()
model=Pipeline([('tfidf',TfidfVectorizer(max_features=60000,ngram_range=(1,2),min_df=3,max_df=.98,sublinear_tf=True)),('classifier',LogisticRegression(C=1,max_iter=250,class_weight='balanced',random_state=20260929))])
model.fit([r['text'] for r in train],[r['label'] for r in train]);prediction=model.predict([r['text'] for r in valid]);gold=[r['label'] for r in valid]
report={'purpose':'domain-disjoint validation baseline; final test not evaluated','train_n':len(train),'validation_n':len(valid),'accuracy':accuracy_score(gold,prediction),'macro_f1':f1_score(gold,prediction,average='macro'),'classification_report':classification_report(gold,prediction,output_dict=True,zero_division=0),'seconds':time.monotonic()-start}
a.output.mkdir(parents=True,exist_ok=True);(a.output/'tfidf_validation.json').write_text(json.dumps(report,indent=2));joblib.dump(model,a.output/'tfidf.joblib');print(json.dumps(report,indent=2))
