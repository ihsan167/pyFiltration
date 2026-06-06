"""Configuration loading for design runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import DesignInputs, FanSpec, FilterSpec, FormaldehydeSpec, ParticleSpec, RoomSpec


def load_design_config(path: str | Path) -> DesignInputs:
    path = Path(path)
    data = _load_mapping(path)
    return DesignInputs(
        room=RoomSpec(**data["room"]),
        particle=ParticleSpec(**data["particle"]),
        formaldehyde=FormaldehydeSpec(**data["formaldehyde"]),
        filter=FilterSpec(**data["filter"]),
        fan=FanSpec(**data["fan"]),
        safety_factor=float(data.get("safety_factor", 1.0)),
    )


def _load_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError("Install PyYAML to read YAML configs, or use JSON.") from exc
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("configuration root must be a mapping")
    required = {"room", "particle", "formaldehyde", "filter", "fan"}
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"configuration missing required sections: {', '.join(missing)}")
    return data
