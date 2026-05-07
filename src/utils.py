from __future__ import annotations
import json
from datetime import datetime

def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))

def normalize_weights(values: dict[str, float]) -> dict[str, float]:
    total = sum(max(v, 0) for v in values.values())
    if total <= 0:
        return {k: 0 for k in values}
    return {k: max(v, 0) / total for k, v in values.items()}

def scenario_to_json(payload: dict) -> str:
    payload = dict(payload)
    payload["exported_at"] = datetime.utcnow().isoformat() + "Z"
    return json.dumps(payload, indent=2)

def load_scenario_json(raw: str) -> dict:
    return json.loads(raw)
