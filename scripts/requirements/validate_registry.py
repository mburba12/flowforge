#!/usr/bin/env python
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
import yaml

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root); errors=[]
 domains={x['code'] for x in yaml.safe_load((root/'specs/architecture/domain-registry.yaml').read_text())['domains']}
 policy=yaml.safe_load((root/'specs/requirements/evidence-policy.yaml').read_text()); statuses=set(policy['status_values'])
 data=yaml.safe_load((root/'specs/requirements/master-requirements.yaml').read_text()); reqs=data.get('requirements',[]); ids=[]
 for x in reqs:
  rid=x.get('id'); ids.append(rid)
  if not re.fullmatch(r'FF-[A-Z]{3}-\d{5}',rid or ''): errors.append(f'invalid id {rid}')
  if x.get('module') not in domains: errors.append(f'{rid}: invalid module')
  if x.get('status') not in statuses: errors.append(f'{rid}: invalid status')
  if not x.get('sources'): errors.append(f'{rid}: no source')
 if len(ids)!=len(set(ids)): errors.append('duplicate IDs')
 known=set(ids)
 for x in reqs:
  for d in x.get('dependencies',[]):
   if d not in known: errors.append(f"{x['id']}: missing dependency {d}")
 manifest=json.loads((root/'specs/extracted/extraction-manifest.json').read_text())
 if manifest.get('total_pages')<3000: errors.append('expected at least 3000 extracted pages')
 if not reqs: errors.append('no requirements generated')
 report={'version':1,'requirements':len(reqs),'pages':manifest.get('total_pages'),'errors':errors,'result':'PASS' if not errors else 'FAIL'}
 out=root/'artifacts/requirements/baseline/validation.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report,indent=2)); return 1 if errors else 0
if __name__=='__main__': sys.exit(main())
