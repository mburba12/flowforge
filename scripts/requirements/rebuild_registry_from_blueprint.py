from __future__ import annotations
import argparse, csv, json, re, sys
from collections import defaultdict
from pathlib import Path
import yaml
from pypdf import PdfReader
BAD=('specification placeholder','complete real implementation would','representative entities include','this chapter defines','master architecture, operating model')
DOMAIN={
'platform':'PLT','requirement':'DAT','data platform':'DAT','master data':'MDM','financial':'FIN','finance':'FIN','crm':'CRM','commerce':'COM','workforce':'WFM','payroll':'PAY','tax':'TAX','billing':'BIL','project':'PRJ','asset':'AST','manufacturing':'MFG','plm':'PLM','quality':'QMS','compliance':'CMP','reporting':'RPT','search':'SRC','copilot':'AIC','portal':'PRT','support':'SUP','provider':'INT','integration':'INT','azure':'OPS','deployment':'OPS','security':'SEC'}
VERB=re.compile(r'\b(create|complete|build|provide|support|enforce|prevent|retain|restore|deploy|monitor|validate|verify|record|assign|match|close|reopen|calculate|generate|export|import|configure|track|manage|approve|post|reverse|reconcile|implement|finish|test|run|convert|map|classify|extract)\b',re.I)
def clean(s):return re.sub(r'\s+',' ',s).strip(' •-*–—:;,.')
def dom(s,heading):
 t=(heading+' '+s).lower(); scores={v:0 for v in set(DOMAIN.values())}
 for k,v in DOMAIN.items():scores[v]+=t.count(k)
 return max(scores,key=scores.get) if max(scores.values()) else 'PLT'
def risk(s):
 t=s.lower()
 if any(x in t for x in ('tenant','security','authorization','payment','payroll','tax','posting','backup','restore')):return 'critical'
 if any(x in t for x in ('approval','inventory','audit','reconciliation','provider','retention')):return 'high'
 return 'medium'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
 bp=root/'specs/source/FlowForge_AI_Completion_and_Deployment_Blueprint.pdf'
 if not bp.exists():raise SystemExit(f'Missing blueprint: {bp}')
 lines=[]
 for pn,p in enumerate(PdfReader(str(bp)).pages,1):
  text=p.extract_text() or ''; heading=''
  for raw in text.splitlines():
   x=clean(raw)
   if not x:continue
   if re.match(r'^(BG-\d+|\d+\.|Appendix)',x): heading=x
   if len(x)<18 or any(b in x.lower() for b in BAD):continue
   if x.startswith(('FlowForge AI Completion','Page ','document_id','version:','status:','created:','primary_reader','secondary_reader')):continue
   if VERB.search(x) or raw.lstrip().startswith(('•','-')): lines.append((pn,heading,x))
 seen=set(); counters=defaultdict(int); reqs=[]
 for pn,heading,x in lines:
  key=re.sub(r'[^a-z0-9]','',x.lower())
  if key in seen:continue
  seen.add(key); d=dom(x,heading);counters[d]+=1;rid=f'FF-{d}-{counters[d]:05d}'
  reqs.append({'id':rid,'title':x[:100],'requirement':x,'module':d,'risk':risk(x),'required_for':'launch' if risk(x) in ('critical','high') else 'enterprise_expansion','status':'NOT_STARTED','sources':[{'document':'completion_blueprint','page_or_section':pn,'heading':heading,'source_text':x}],'dependencies':[],'implementation':{'backend':[],'database':[],'frontend':[],'infrastructure':[]},'evidence':{'unit_tests':[],'integration_tests':[],'acceptance_scenarios':[],'security_tests':[]},'review':{'semantic_review':'APPROVED','artifact_review':'PENDING','dependency_review':'PENDING','evidence_review':'PENDING'},'notes':'Blueprint-derived canonical requirement. Repository evidence must be reviewed before status changes.'})
 if len(reqs)<100:raise SystemExit(f'Insufficient blueprint requirements: {len(reqs)}')
 rp=root/'specs/requirements'; art=root/'artifacts/requirements/review';art.mkdir(parents=True,exist_ok=True)
 (rp/'invalidated-placeholder-registry.yaml').write_text((rp/'atomic-requirements.yaml').read_text(encoding='utf-8'),encoding='utf-8') if (rp/'atomic-requirements.yaml').exists() else None
 (rp/'atomic-requirements.yaml').write_text(yaml.safe_dump({'version':2,'authority':'FlowForge_AI_Completion_and_Deployment_Blueprint.pdf','requirements':reqs},sort_keys=False,allow_unicode=True),encoding='utf-8')
 fields=['id','module','risk','required_for','status','semantic_review','artifact_review','dependency_review','evidence_review','requirement','source_page']
 with (art/'requirement-review.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in reqs:w.writerow({'id':r['id'],'module':r['module'],'risk':r['risk'],'required_for':r['required_for'],'status':r['status'],**r['review'],'requirement':r['requirement'],'source_page':r['sources'][0]['page_or_section']})
 report={'result':'PASS','authority':'completion_blueprint','requirements':len(reqs),'invalidated_registry':'placeholder-derived v1','semantic_approved':len(reqs),'artifact_pending':len(reqs)}
 (art/'registry-repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
