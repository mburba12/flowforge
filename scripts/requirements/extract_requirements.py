#!/usr/bin/env python
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from pypdf import PdfReader

REQ_PATTERNS = re.compile(r"\b(shall|must|required|requires|should|will support|must not|shall not)\b", re.I)
HEAD_PATTERNS = re.compile(r"^(chapter|section|part|module|phase|wave|\d+(?:\.\d+){0,4})\b", re.I)
DOMAIN_TERMS = {
 'PLT':['tenant','identity','authentication','authorization','workflow','audit','document','notification','session','permission'],
 'DAT':['data lake','data warehouse','data governance','data quality','catalog','lineage'],
 'MDM':['party','customer','vendor','organization','address','contact','identifier','master data'],
 'FIN':['ledger','journal','accounts payable','accounts receivable','bank','reconciliation','financial'],
 'CRM':['lead','opportunity','crm','campaign','quote'],
 'COM':['inventory','procurement','purchase order','warehouse','shipping','sales order','product','sku'],
 'WFM':['worker','employee','recruit','performance','training','benefit','leave','timecard'],
 'PAY':['payroll','gross-to-net','earning','deduction','pay period'],
 'TAX':['tax','jurisdiction','filing','remittance'],
 'BIL':['subscription','billing','entitlement','proration'],
 'PRJ':['project','milestone','utilization'],
 'AST':['fixed asset','depreciation','impairment'],
 'MFG':['manufacturing','bom','routing','mrp','work order','work center'],
 'PLM':['product lifecycle','engineering change','item revision'],
 'QMS':['quality','inspection','nonconformance','capa','complaint','recall'],
 'RPT':['report','dashboard','metric','analytics'],
 'SRC':['search','indexing'],
 'AIC':['copilot','artificial intelligence',' ai ','grounded','prompt'],
 'PRT':['portal'], 'SUP':['support case','incident'],
 'INT':['integration','provider','oauth','webhook'],
 'OPS':['azure','deployment','backup','restore','container app','monitoring'],
 'SEC':['security','threat','vulnerability','encryption','mfa','row-level security']}

def sha(path: Path)->str:
 h=hashlib.sha256();
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def clean(s:str)->str: return re.sub(r'\s+',' ',s).strip()
def domain(text:str)->str:
 t=' '+text.lower()+' '; scores={k:sum(t.count(x) for x in v) for k,v in DOMAIN_TERMS.items()}; best=max(scores,key=scores.get); return best if scores[best] else 'PLT'
def risk(text:str)->str:
 t=text.lower()
 if any(x in t for x in ['tenant isolation','payment','payroll','tax filing','security','authorization','financial posting','backup','restore']): return 'critical'
 if any(x in t for x in ['approval','inventory','audit','retention','reconciliation','provider']): return 'high'
 return 'medium' if len(text)>100 else 'low'
def segment(page_text:str):
 lines=[clean(x) for x in page_text.splitlines() if clean(x)]
 heading=''
 for line in lines:
  is_heading=bool(HEAD_PATTERNS.search(line) and len(line)<160)
  if is_heading:
   heading=line
   continue
  # The source specifications are primarily capability catalogs rather than
  # RFC-style shall statements. Preserve every substantive catalog line as a
  # candidate, while filtering obvious page furniture and fragments.
  if len(line)<25 or len(line)>500: continue
  if re.fullmatch(r'(page\s+)?\d+',line,re.I): continue
  if line.lower().startswith(('flowforge mega specification','flowforge ultimate master specification','flowforge enterprise build bible')): continue
  parts=re.split(r'(?<=[.!?;])\s+(?=[A-Z0-9])',line)
  for part in parts:
   part=clean(part).lstrip('•-*–—0123456789. )(').strip()
   if len(part)>=25: yield heading,part

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root)
 src=root/'specs/source'; out=root/'specs/extracted'; req=root/'specs/requirements'; out.mkdir(parents=True,exist_ok=True)
 docs=[('mega_specification','FlowForge_Mega_Specification_Volume.pdf'),('ultimate_master_specification','FlowForge_Ultimate_Master_Specification.pdf'),('enterprise_build_bible','FlowForge_Enterprise_Build_Bible.pdf')]
 manifest={'version':1,'documents':[],'total_pages':0,'candidate_count':0}; candidates=[]; seen_candidate_text=set()
 for key,name in docs:
  path=src/name
  if not path.exists(): raise SystemExit(f'Missing source PDF: {path}')
  reader=PdfReader(str(path)); page_file=out/f'{key}.jsonl'
  with page_file.open('w',encoding='utf-8') as pf:
   for idx,p in enumerate(reader.pages,1):
    text=p.extract_text() or ''; pf.write(json.dumps({'document':key,'page':idx,'text':text},ensure_ascii=False)+'\n')
    for heading,statement in segment(text):
     fp=hashlib.sha256(clean(statement).lower().encode()).hexdigest()
     if fp in seen_candidate_text: continue
     seen_candidate_text.add(fp)
     candidates.append({'candidate_id':f'CAND-{len(candidates)+1:07d}','source_document':key,'source_page':idx,'source_heading':heading,'source_text':statement,'normalized_requirement':statement,'proposed_domain':domain(statement),'proposed_risk':risk(statement),'status':'NOT_STARTED'})
  manifest['documents'].append({'key':key,'file':f'specs/source/{name}','pages':len(reader.pages),'sha256':sha(path),'extracted_file':f'specs/extracted/{key}.jsonl'})
  manifest['total_pages']+=len(reader.pages)
 with (out/'extraction-manifest.json').open('w',encoding='utf-8') as f: json.dump(manifest,f,indent=2)
 with (req/'candidates.jsonl').open('w',encoding='utf-8') as f:
  for c in candidates: f.write(json.dumps(c,ensure_ascii=False)+'\n')
 manifest['candidate_count']=len(candidates)
 (out/'extraction-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print(f"pages={manifest['total_pages']} candidates={len(candidates)}")
if __name__=='__main__': main()
