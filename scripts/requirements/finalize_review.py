#!/usr/bin/env python
from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
import yaml
ALLOWED_REVIEW={'PENDING','APPROVED','REJECTED','NEEDS_SPLIT','NEEDS_DECISION'}
COMPLETE={'VERIFIED_EXISTING','LIVE_ACCEPTED','EXTERNALLY_BLOCKED','APPROVED_DEFERRED','NOT_APPLICABLE'}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--allow-pending',action='store_true'); a=ap.parse_args(); root=Path(a.root); rp=root/'specs/requirements'; art=root/'artifacts/requirements/review'; data=yaml.safe_load((rp/'atomic-requirements.yaml').read_text(encoding='utf-8')); reqs=data['requirements']; csvp=art/'requirement-review.csv'; rows={x['id']:x for x in csv.DictReader(csvp.open(encoding='utf-8-sig'))}; errors=[]
 for r in reqs:
  row=rows.get(r['id'])
  if not row: errors.append(f"{r['id']}: missing review row"); continue
  for col in ('semantic_review','artifact_review','dependency_review','evidence_review'):
   value=row[col]
   if value not in ALLOWED_REVIEW: errors.append(f"{r['id']}: invalid {col}={value}")
   if not a.allow_pending and value!='APPROVED': errors.append(f"{r['id']}: {col} not APPROVED")
  r['status']=row['status']; r['review']={k:row[k] for k in ('semantic_review','artifact_review','dependency_review','evidence_review')}
 conflicts=yaml.safe_load((rp/'conflicts.yaml').read_text(encoding='utf-8')).get('conflicts',[])
 unresolved=[x for x in conflicts if x.get('status') not in ('RESOLVED','APPROVED_DEFERRED')]
 if unresolved: errors.append(f'unresolved conflicts={len(unresolved)}')
 report={'version':1,'atomic_requirements':len(reqs),'pending_allowed':a.allow_pending,'errors':errors,'result':'PASS' if not errors else 'FAIL','complete_now':sum(1 for r in reqs if r['status'] in COMPLETE)}
 (art/'bg00-completion.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 if not errors: (rp/'atomic-requirements.yaml').write_text(yaml.safe_dump({'version':1,'requirements':reqs},sort_keys=False,allow_unicode=True),encoding='utf-8')
 print(json.dumps(report,indent=2)); return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
