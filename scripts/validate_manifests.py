#!/usr/bin/env python3
"""Validate environment manifests and team configs before CI plans or deploys.

Standard library only, so it needs no hashed pip requirements.
Run from the repo root:  python scripts/validate_manifests.py
"""

import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

# Policy limits: edit these to match your rules.
ALLOWED_INSTANCE_TYPES = {"t3.micro", "t3.small", "t3.medium"}
ALLOWED_KEYS = {"envName", "instanceType", "requestedBy"}
REQUIRED_KEYS = {"envName", "requestedBy"}
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")

errors = []


def fail(path, msg):
    errors.append(f"{path.relative_to(REPO)}: {msg}")


def load(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        fail(path, f"cannot read as JSON ({e})")
        return None


# Team configs must parse and name the team after the file.
team_configs = {}
for f in sorted((REPO / "config").glob("*.json")):
    cfg = load(f)
    if cfg is None:
        continue
    if cfg.get("team") != f.stem:
        fail(f, f"'team' is {cfg.get('team')!r}, expected {f.stem!r}")
    team_configs[f.stem] = cfg

# Manifests.
for team_dir in sorted((REPO / "teams").iterdir()):
    if not team_dir.is_dir():
        continue
    team = team_dir.name
    if team not in team_configs:
        fail(team_dir / "envs", f"no config/{team}.json for this team")
    for f in sorted((team_dir / "envs").glob("*.json")):
        m = load(f)
        if m is None:
            continue
        if not isinstance(m, dict):
            fail(f, "manifest must be a JSON object")
            continue
        for k in sorted(REQUIRED_KEYS - m.keys()):
            fail(f, f"missing required field {k!r}")
        for k in sorted(m.keys() - ALLOWED_KEYS):
            fail(f, f"unknown field {k!r}")
        name = m.get("envName")
        if name is not None:
            if name != f.stem:
                fail(f, f"envName {name!r} must match the filename {f.stem!r}")
            if not NAME_RE.match(str(name)):
                fail(f, f"envName {name!r} must be lowercase letters, digits, hyphens")
            if not str(name).startswith(team):
                fail(f, f"envName {name!r} must start with the team name {team!r}")
        it = m.get("instanceType")
        if it is not None and it not in ALLOWED_INSTANCE_TYPES:
            fail(f, f"instanceType {it!r} not in {sorted(ALLOWED_INSTANCE_TYPES)}")
        rb = m.get("requestedBy")
        if rb is not None and not (isinstance(rb, str) and rb.strip()):
            fail(f, "requestedBy must be a non-empty string")

if errors:
    print("Manifest validation failed:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print("Manifest validation passed.")
