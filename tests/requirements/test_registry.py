import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_policy_and_domains_parse():
    assert (
        yaml.safe_load((ROOT / "specs/requirements/evidence-policy.yaml").read_text())["version"]
        == 1
    )
    assert (
        len(
            yaml.safe_load((ROOT / "specs/architecture/domain-registry.yaml").read_text())[
                "domains"
            ]
        )
        >= 20
    )


def test_registry_ids_and_sources():
    p = ROOT / "specs/requirements/master-requirements.yaml"
    if not p.exists():
        return
    reqs = yaml.safe_load(p.read_text()).get("requirements", [])
    ids = [x["id"] for x in reqs]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"FF-[A-Z]{3}-\d{5}", x) for x in ids)
    assert all(x["sources"] for x in reqs)


def test_validation_result_when_generated():
    p = ROOT / "artifacts/requirements/baseline/validation.json"
    if p.exists():
        assert json.loads(p.read_text())["result"] == "PASS"
