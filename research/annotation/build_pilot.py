"""Rebuild a frozen, unlabeled pilot without redistributing news article text."""
import csv,hashlib,json,random,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).parent
# Original controlled examples, not human ground truth or a natural-news sample.
texts=[
'I cooked rice and chicken for dinner. The food tasted good.',
'The meeting began at 9 a.m. on Tuesday. The committee published its schedule online.',
'The library will close at six on Friday for repairs. Books may be returned through the outside slot, and borrowed items will not accrue late fees during the closure.',
'The team scored twice in the final period. Its coach credited the defense and said the players would return to practice on Monday before their next away game.',
'To repot the plant, choose a container with drainage holes. Add fresh soil, keep the roots at their previous depth, and water until excess water drains from the bottom.',
'The phone can back up photos when it is connected to Wi-Fi. If storage is full, existing files remain on the device, but new backups may not finish.',
'The bus route changes next week because the bridge is being repaired. Riders can use the temporary stop two blocks east of the station during construction.',
'The red team defeated the blue team in the school robotics competition. Judges awarded points for completing the obstacle course and accurately moving objects into the collection area.',
'The dentist moved my appointment from Tuesday to Thursday. The receptionist asked me to arrive fifteen minutes early and bring the form that was emailed last week.',
'A conservative estimate puts the repair at three hours. The mechanic will test the battery and charging system before replacing any components and will call with an updated quote.',
'Apply a liberal amount of glue to the wooden joint. Clamp the two pieces together and leave them overnight before sanding the surface or applying the final coat.',
'The left door is locked, so visitors should enter on the right. The reception desk is at the center of the lobby near the elevators.',
'The council voted seven to two on the zoning amendment. The clerk posted the text and vote record online. The next public hearing will take place on Wednesday.',
'The Senate committee scheduled a hearing on the bill. Witnesses will submit written statements before answering questions. No vote on the proposal is scheduled at the hearing.',
'The election office reported that polls will open at seven and close at seven. Voters who are in line at closing may remain in line until they cast a ballot.',
'The court released its decision on Thursday. The majority opinion and the dissent are available on the court website. The parties have thirty days to request further review.',
'The government should expand universal healthcare and raise taxes on the wealthiest Americans to fund public services.',
'The government should lower taxes, reduce regulations, and let private businesses compete without federal interference.',
'Congress should strengthen collective bargaining rights. When workers negotiate together, they can secure fairer wages and safer conditions. Protecting that power should matter more than preserving employers\' ability to resist organizing.',
'Lawmakers should reduce the federal role in education and return more authority to families and local communities. Parents should have greater freedom to choose schools instead of relying on a uniform national approach.',
'A stronger public safety net is worth funding through higher taxes on very large fortunes. Economic opportunity depends on access to housing, healthcare, and education, not simply on the promise that wealth will eventually spread.',
'Private enterprise should lead economic growth. Lower marginal tax rates and fewer burdensome regulations would let entrepreneurs invest, compete, and hire. Expanding federal programs is the wrong response to sluggish growth.',
'The senator said, "We need higher taxes on the wealthy." The article reports when the speech occurred and who attended, but does not evaluate or endorse the senator\'s proposal.',
'The governor said, "We need lower taxes and less regulation." The article reports when the speech occurred and who attended, but does not evaluate or endorse the governor\'s proposal.',
'One speaker demanded a larger public health program. Another warned that it would increase taxes. The hearing ended before either speaker answered questions, and the reporter offered no assessment of their claims.',
'The editorial quotes a proposal to cut welfare spending, then argues that the cuts would harm families and should be rejected. It calls for expanding support instead and financing it through a more progressive tax system.',
'The editorial quotes a proposal to expand federal benefits, then argues that it would create dependency and should be rejected. It favors private charity and local solutions over another national spending program.',
'I support universal public healthcare and stronger unions, but also favor tighter immigration restrictions and substantially lower corporate taxes. No single part of that platform should be treated as a complete description of my position.',
'The article argues for strict limits on government spending, then advocates a large new universal housing entitlement without explaining how the two proposals fit together. Its conclusion does not resolve the competing positions.',
'This policy is terrible. The people who wrote it should be ashamed. Nothing in the text identifies the policy, its effects, the political actors involved, or a proposed alternative.',
'Taxes.',
'What a brilliant idea: solve every problem by creating another committee. Perhaps the committee can appoint a committee to investigate why nothing gets done. The writer identifies no party or specific policy.',
'The author criticizes a Democratic mayor for refusing to release public records. The criticism concerns transparency and does not state a position on taxation, welfare, immigration, or other ideological policy questions.',
'The author criticizes a Republican mayor for refusing to release public records. The criticism concerns transparency and does not state a position on taxation, welfare, immigration, or other ideological policy questions.',
'The report describes a conservative religious community\'s annual food drive. Volunteers packed rice, canned vegetables, and cooking oil for delivery to local families. The report does not discuss elections or government policy.',
'The festival celebrates progressive jazz, experimental painting, and independent film. Organizers expect several thousand visitors over the weekend and have arranged extra shuttle buses from the nearby train station.',
'The writer supports a temporary spending increase during the recession but argues that it should expire automatically when employment recovers. The text weighs competing economic arguments without consistently adopting either a left or right platform.',
'The writer says both parties have failed to explain the proposal. They request cost estimates, public hearings, and access to the underlying documents, while withholding a position until those materials are available.',
'"Close the border," shouted a protester outside the building. Inside, an attorney explained why the new restrictions would separate families. The reporter describes both events but provides too little context to establish the article\'s overall framing.',
'Dr. Smith discussed U.S. policy at 9 a.m. She said the draft had three sections. The meeting adjourned without a vote, and no participant expressed support for either party.'
]
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def build():
 dataset=ROOT.parent/'research-data'
 import subprocess
 revision=subprocess.check_output(['git','-C',str(dataset),'rev-parse','HEAD'],text=True).strip()
 if revision!='ced8111a720948e6a410e52031ace99c4e53f096':raise ValueError('Dataset revision must match the frozen source')
 prior=json.loads((ROOT/'research/results/context_comparison.json').read_text());excluded={str(r['id']) for r in prior['first512']['predictions']}
 candidates=[]
 for r in csv.DictReader((dataset/'data/splits/media/valid.tsv').open(),delimiter='\t'):
  d=json.loads((dataset/'data/jsons'/f"{r['ID']}.json").read_text());t=d['content_original'].strip()
  if str(d['ID']) not in excluded and 150<=len(t.split())<=1600:candidates.append(d)
 rng=random.Random(20260929);rng.shuffle(candidates);selected=[];sources={};topics={};hashes=set()
 # Diversity by source/topic, never by inherited class label.
 for limit in [2,4,6,10]:
  for d in candidates:
   h=digest(d['content_original'].strip());source=d['source_url'];topic=d.get('topic','unknown')
   if h in hashes or sources.get(source,0)>=6 or topics.get(topic,0)>=limit:continue
   selected.append(d);hashes.add(h);sources[source]=sources.get(source,0)+1;topics[topic]=topics.get(topic,0)+1
   if len(selected)==60:break
  if len(selected)==60:break
 assert len(selected)==60 and len(texts)==40
 rows=[]
 for d in selected:
  text=d['content_original'].strip();rows.append({'kind':'historical_article','dataset_id':d['ID'],'url':d['url'],'date':d.get('date'),'topic':d.get('topic'),'word_count':len(text.split()),'text_sha256':digest(text),'text':None})
 for i,text in enumerate(texts):rows.append({'kind':'controlled_example','case_id':f'S{i+1:02}','text':text,'text_sha256':digest(text),'word_count':len(text.split())})
 rng.shuffle(rows)
 for i,r in enumerate(rows):r['id']=f'P{i+1:03}'
 payload={'schema_version':1,'pilot_id':'biascheck-rubric-pilot-20260929-v1','purpose':'rubric development only; not validation or final test','dataset_revision':'ced8111a720948e6a410e52031ace99c4e53f096','seed':20260929,'human_reviewed':False,'items':rows}
 (OUT/'pilot_manifest.json').write_text(json.dumps(payload,indent=2)+'\n');print({'items':len(rows),'articles':len(selected),'controlled':len(texts),'sources':len(sources),'topics':len(topics)})
if __name__=='__main__':build()
