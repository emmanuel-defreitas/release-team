"""Export standalone specs and JSON Schemas from the canonical registry/models."""

import argparse
import json
from pathlib import Path

import yaml

from release_team.cli import SCHEMAS
from release_team.specs import load_registry

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
assets = Path(__file__).resolve().parents[1] / "src/release_team/assets"
registry = load_registry(assets / "registry.yaml")
outputs = {
    assets / "schemas" / f"{name}.schema.json": json.dumps(model.model_json_schema(), indent=2)
    + "\n"
    for name, model in SCHEMAS.items()
}
for kind, specs in (("agents", registry.agents), ("skills", registry.skills)):
    for spec in specs:
        outputs[assets / kind / f"{spec.metadata.id}.yaml"] = yaml.safe_dump(
            spec.model_dump(mode="json"), sort_keys=False
        )
for path, content in outputs.items():
    if args.check:
        if not path.exists() or path.read_text() != content:
            raise SystemExit(f"stale export: {path.relative_to(assets)}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
