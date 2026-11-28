#!/usr/bin/env python
from __future__ import annotations
import argparse, json, re
from pathlib import Path
import yaml
EXT={'.py','.ts','.tsx','.js','.jsx','.ps1','.md','.json','.yaml','.yml','.bicep','.toml'}
def words(s): return {x for x in re.findall(r'[a-z0-9_]{4,}',s.lower()) if x not in {'shall','must','should','system','flowforge','required','support','allows','allow'}}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root); reqp=root/'specs/requirements/master-requirements.yaml'
 data=yaml.safe_load(reqp.read_text(encoding='utf-8')); reqs=data['requirements']; artifacts=[]
 for base,kind in [('src','backend'),('tests','test'),('web/src','frontend'),('scripts','script'),('infra','infrastructure'),('migrations','migration')]:
  p=root/base
  if not p.exists(): continue
  for f in p.rglob('*'):
   if f.is_file() and f.suffix.lower() in EXT and not any(x in f.parts for x in ['node_modules','.next','__pycache__']):
    txt=f.read_text(encoding='utf-8-sig',errors='ignore')[:500000]; artifacts.append((str(f.relative_to(root)).replace('\\','/'),kind,words(str(f)+' '+txt)))
 output=[]; backlog=[]
 for r in reqs:
  keys=words(r['requirement']); scored=[]
  for path,kind,tokens in artifacts:
   score=len(keys & tokens)
   if score>=max(2,min(5,len(keys)//4)): scored.append((score,path,kind))
  scored=sorted(scored,reverse=True)[:12]
  status='PARTIAL' if scored else 'MISSING_FEATURE'
  output.append({'requirement_id':r['id'],'status':status,'candidate_artifacts':[{'path':p,'kind':k,'score':s} for s,p,k in scored],'review_required':True})
  backlog.append({'requirement_id':r['id'],'module':r['module'],'risk':r['risk'],'action':'VERIFY' if scored else 'BUILD','status':status})
 art=root/'artifacts/requirements/baseline'; art.mkdir(parents=True,exist_ok=True)
 (art/'repository-crosswalk.json').write_text(json.dumps({'version':1,'mappings':output},indent=2),encoding='utf-8')
 (root/'specs/requirements/build-backlog.yaml').write_text(yaml.safe_dump({'version':1,'items':backlog},sort_keys=False),encoding='utf-8')
 (art/'orphaned-artifacts.json').write_text(json.dumps({'version':1,'note':'Manual reverse mapping required after candidate review','artifacts':[{'path':p,'kind':k} for p,k,_ in artifacts]},indent=2),encoding='utf-8')
 print(f'requirements={len(reqs)} artifacts={len(artifacts)}')
if __name__=='__main__': main()
