from pathlib import Path
import json,yaml
ROOT=Path(__file__).resolve().parents[2]
def test_atomic_registry_if_generated():
 p=ROOT/'specs/requirements/atomic-requirements.yaml'
 if p.exists():
  r=yaml.safe_load(p.read_text())['requirements']; assert r; assert len({x['id'] for x in r})==len(r)
def test_refinement_summary_if_generated():
 p=ROOT/'artifacts/requirements/review/refinement-summary.json'
 if p.exists(): assert json.loads(p.read_text())['atomic_requirements']>0
