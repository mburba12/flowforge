#!/usr/bin/env python
from __future__ import annotations
import argparse, json, re, hashlib
from collections import defaultdict
from pathlib import Path
import yaml

def norm(s): return re.sub(r'[^a-z0-9 ]',' ',s.lower()).strip()
def fingerprint(s): return hashlib.sha256(norm(s).encode()).hexdigest()[:16]
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); a=ap.parse_args(); root=Path(a.root); r=root/'specs/requirements'
 candidates=[json.loads(x) for x in (r/'candidates.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
 grouped=defaultdict(list)
 for c in candidates: grouped[fingerprint(c['normalized_requirement'])].append(c)
 counters=defaultdict(int); requirements=[]; duplicate_groups=[]
 for fp,items in grouped.items():
  canonical=items[0]; dom=canonical['proposed_domain']; counters[dom]+=1; rid=f"FF-{dom}-{counters[dom]:05d}"
  requirements.append({'id':rid,'title':canonical['normalized_requirement'][:100],'requirement':canonical['normalized_requirement'],'module':dom,'risk':canonical['proposed_risk'],'required_for':'enterprise_expansion','status':'NOT_STARTED','sources':[{'document':x['source_document'],'page_or_section':x['source_page'],'heading':x['source_heading'],'source_text':x['source_text']} for x in items],'dependencies':[],'implementation':{'backend':[],'database':[],'frontend':[],'infrastructure':[]},'evidence':{'unit_tests':[],'integration_tests':[],'acceptance_scenarios':[],'security_tests':[]},'provider_dependency':None,'owner':None,'notes':None})
  if len(items)>1: duplicate_groups.append({'canonical_requirement':rid,'candidate_ids':[x['candidate_id'] for x in items],'fingerprint':fp})
 (r/'master-requirements.yaml').write_text(yaml.safe_dump({'version':1,'requirements':requirements},sort_keys=False,allow_unicode=True),encoding='utf-8')
 (r/'duplicates.yaml').write_text(yaml.safe_dump({'version':1,'duplicate_groups':duplicate_groups},sort_keys=False),encoding='utf-8')
 modules=defaultdict(list)
 for x in requirements: modules[x['module']].append(x)
 for mod,items in modules.items(): (r/'modules'/f'{mod.lower()}.yaml').write_text(yaml.safe_dump({'version':1,'module':mod,'requirements':items},sort_keys=False,allow_unicode=True),encoding='utf-8')
 print(f'requirements={len(requirements)} duplicate_groups={len(duplicate_groups)}')
if __name__=='__main__': main()
