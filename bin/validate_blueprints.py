#!/usr/bin/env python3
"""Validate Home Assistant blueprint files against HA's own schema.

Runs *inside* the official Home Assistant container so it uses the exact
loader (handling the ``!input`` tag) and the real ``BLUEPRINT_SCHEMA`` /
``Blueprint`` model that HA applies when importing a blueprint. This catches
malformed metadata, bad input selectors, a missing ``blueprint:`` block or a
wrong ``domain`` before anyone imports the blueprint.

Usage:  python bin/validate_blueprints.py <file.yaml> [<file.yaml> ...]
Exit code is non-zero if any file fails.
"""

from __future__ import annotations

import sys

from homeassistant.components.blueprint.models import Blueprint
from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.util.yaml import load_yaml


def validate(path: str) -> str | None:
    """Return an error string for *path*, or None when it is valid."""
    try:
        data = load_yaml(path)
    except Exception as err:  # noqa: BLE001 - report any load failure
        return f"YAML load error: {err}"

    if not isinstance(data, dict) or "blueprint" not in data:
        return "missing top-level 'blueprint:' block"

    try:
        # Constructing a Blueprint runs BLUEPRINT_SCHEMA against the data and
        # validates the declared inputs; expected_domain checks the domain key.
        Blueprint(
            data,
            path=path,
            expected_domain=data["blueprint"].get("domain"),
            schema=BLUEPRINT_SCHEMA,
        )
    except Exception as err:  # noqa: BLE001 - surface HA's validation error
        return str(err)

    return None


def main(paths: list[str]) -> int:
    if not paths:
        print("usage: validate_blueprints.py <file.yaml> [...]", file=sys.stderr)
        return 2

    failed = False
    for path in paths:
        error = validate(path)
        if error is None:
            print(f"OK    {path}")
        else:
            failed = True
            print(f"FAIL  {path}: {error}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
