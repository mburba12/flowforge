#!/usr/bin/env python
from __future__ import annotations
import argparse,json
from collections import defaultdict
from pathlib import Path
import yaml
ORDER=['PLT','SEC','DAT','MDM','FIN','CRM','COM','WFM','PAY','TAX','BIL','PRJ','AST','PLM','MFG','QMS','CMP','RPT','SRC','AIC','PRT','SUP','INT','OPS']
ACTION={'MISSING_FOUNDATION':'BUILD_FOUNDATION','MISSING_FEATURE':'BUILD','EXISTING_NEEDS_REPAIR':'REPAIR','EXISTING_NEEDS_INTEGRATION':'INTEGRATE','PARTIAL':'COMPLETE','INTERFACE_ONLY':'COMPLETE_ADAPTER','VERIFIED_EXISTING':'VERIFY_EVIDENCE','LIVE_ACCEPTED':'PRESERVE'}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root); rp=root/'specs/requirements'; reqs=yaml.safe_load((rp/'atomic-requirements.yaml').read_text(encoding='utf-8'))['requirements']; rank={x:i for i,x in enumerate(ORDER)}; risk={'critical':0,'high':1,'medium':2,'low':3}; pri={'launch':0,'post_launch':1,'enterprise_expansion':2}
 items=[]
 for r in reqs:
  items.append({'sequence':0,'requirement_id':r['id'],'module':r['module'],'risk':r['risk'],'release_priority':r['required_for'],'current_status':r['status'],'action':ACTION.get(r['status'],'REVIEW'),'dependencies':r.get('dependencies',[]),'blocked_by_review':any(v!='APPROVED' for v in r.get('review',{}).values())})
 items.sort(key=lambda x:(rank.get(x['module'],99),pri.get(x['release_priority'],9),risk.get(x['risk'],9),x['requirement_id']))
 for i,x in enumerate(items,1):x['sequence']=i
 (rp/'final-build-queue.yaml').write_text(yaml.safe_dump({'version':1,'items':items},sort_keys=False),encoding='utf-8')
 print(f'queue_items={len(items)} blocked_by_review={sum(x["blocked_by_review"] for x in items)}')
if __name__=='__main__':main()
