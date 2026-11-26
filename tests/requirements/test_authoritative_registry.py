from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]
def test_no_placeholder_requirements():
 p=ROOT/'specs/requirements/atomic-requirements.yaml'
 if not p.exists():return
 d=yaml.safe_load(p.read_text()); assert d.get('authority')=='FlowForge_AI_Completion_and_Deployment_Blueprint.pdf'; assert len(d['requirements'])>=100
 assert not any('specification placeholder' in x['requirement'].lower() for x in d['requirements'])
