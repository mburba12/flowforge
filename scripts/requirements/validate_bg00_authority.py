import argparse,json,sys
from pathlib import Path
import yaml
BAD=('specification placeholder','complete real implementation would','authoring each artifact in detail')
ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);a=ap.parse_args();root=Path(a.root)
p=root/'specs/requirements/atomic-requirements.yaml';d=yaml.safe_load(p.read_text(encoding='utf-8'));reqs=d['requirements'];errors=[]
if d.get('authority')!='FlowForge_AI_Completion_and_Deployment_Blueprint.pdf':errors.append('invalid authority')
if len(reqs)<100:errors.append('too few requirements')
for r in reqs:
 if any(x in r['requirement'].lower() for x in BAD):errors.append(f"placeholder {r['id']}")
 if r['review']['semantic_review']!='APPROVED':errors.append(f"semantic pending {r['id']}")
report={'result':'PASS' if not errors else 'FAIL','requirements':len(reqs),'errors':errors};(root/'artifacts/requirements/review/bg00-authority-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(1 if errors else 0)
