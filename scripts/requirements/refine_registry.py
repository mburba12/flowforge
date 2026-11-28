#!/usr/bin/env python
from __future__ import annotations
import argparse,csv,json,re
from collections import defaultdict
from pathlib import Path
import yaml
SPLIT=re.compile(r'\s*(?:;|\n|\band\b|\bas well as\b|,)\s*',re.I)
VERBS=re.compile(r'\b(create|read|view|list|search|update|delete|approve|reject|submit|post|reverse|reconcile|calculate|generate|export|import|notify|schedule|configure|track|manage|support|enforce|prevent|retain|restore|deploy|monitor|validate|verify|record|assign|match|close|reopen|pay|file|ship|receive)\b',re.I)
CRITICAL=('tenant','authorization','payment','payroll','tax','posting','backup','restore','security','credential','financial')
HIGH=('approval','inventory','audit','retention','reconciliation','provider','personal data','document')
def clean(x): return re.sub(r'\s+',' ',x).strip(' .;:-')
def atomic_parts(text):
 parts=[clean(x) for x in SPLIT.split(text) if len(clean(x))>=18]
 good=[x for x in parts if VERBS.search(x)]
 return good if len(good)>=2 else [clean(text)]
def risk(t):
 l=t.lower()
 if any(x in l for x in CRITICAL): return 'critical'
 if any(x in l for x in HIGH): return 'high'
 return 'medium' if len(t)>80 else 'low'
def priority(t):
 l=t.lower()
 if any(x in l for x in ('tenant','auth','ledger','journal','audit','workflow','master data','customer','vendor','inventory','payroll','tax')): return 'launch'
 if any(x in l for x in ('manufactur','quality','portal','copilot','project','subscription','asset')): return 'post_launch'
 return 'enterprise_expansion'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root); rp=root/'specs/requirements'; art=root/'artifacts/requirements/review'; art.mkdir(parents=True,exist_ok=True)
 master=yaml.safe_load((rp/'master-requirements.yaml').read_text(encoding='utf-8')); crossp=root/'artifacts/requirements/baseline/repository-crosswalk.json'; cross=json.loads(crossp.read_text(encoding='utf-8')) if crossp.exists() else {'mappings':[]}; mappings={x['requirement_id']:x for x in cross.get('mappings',[])}
 counters=defaultdict(int); out=[]; parent_links=[]
 for parent in master.get('requirements',[]):
  pieces=atomic_parts(parent['requirement'])
  for piece in pieces:
   mod=parent['module']; counters[mod]+=1; rid=f"FF-{mod}-{counters[mod]:05d}"
   match=mappings.get(parent['id'],{}); candidates=match.get('candidate_artifacts',[])
   current='PARTIAL' if candidates else 'MISSING_FEATURE'
   req={**parent,'id':rid,'parent_requirement_id':parent['id'],'title':piece[:100],'requirement':piece,'risk':risk(piece),'required_for':priority(piece),'status':current,'review':{'semantic_review':'PENDING','artifact_review':'PENDING','dependency_review':'PENDING','evidence_review':'PENDING'},'candidate_artifacts':candidates}
   out.append(req); parent_links.append({'parent':parent['id'],'child':rid})
 (rp/'atomic-requirements.yaml').write_text(yaml.safe_dump({'version':1,'requirements':out},sort_keys=False,allow_unicode=True),encoding='utf-8')
 (rp/'parent-child-crosswalk.yaml').write_text(yaml.safe_dump({'version':1,'links':parent_links},sort_keys=False),encoding='utf-8')
 fields=['id','parent_requirement_id','module','risk','required_for','status','semantic_review','artifact_review','dependency_review','evidence_review','requirement','source_count','candidate_artifact_count']
 with (art/'requirement-review.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
  for x in out: w.writerow({'id':x['id'],'parent_requirement_id':x['parent_requirement_id'],'module':x['module'],'risk':x['risk'],'required_for':x['required_for'],'status':x['status'],**x['review'],'requirement':x['requirement'],'source_count':len(x['sources']),'candidate_artifact_count':len(x['candidate_artifacts'])})
 summary={'version':1,'atomic_requirements':len(out),'parents':len(master.get('requirements',[])),'by_module':{},'by_risk':{},'by_priority':{},'pending_reviews':len(out)*4}
 for key,field in [('by_module','module'),('by_risk','risk'),('by_priority','required_for')]:
  d=defaultdict(int)
  for x in out:d[x[field]]+=1
  summary[key]=dict(sorted(d.items()))
 (art/'refinement-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
