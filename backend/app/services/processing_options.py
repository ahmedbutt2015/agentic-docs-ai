import json
from typing import Any, Dict, List, Optional


PROCESSING_OPTION_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "key": "extract_entities",
        "label": "Entity Extraction",
        "default": True,
    },
    {
        "key": "index_for_chat",
        "label": "Index for Chat",
        "default": True,
    },
    {
        "key": "run_compliance_check",
        "label": "Compliance Scoring",
        "default": True,
    },
]

PROCESSING_OPTION_LABELS = {
    option["key"]: option["label"] for option in PROCESSING_OPTION_DEFINITIONS
}
DEFAULT_PROCESSING_OPTIONS = {
    option["key"]: bool(option["default"]) for option in PROCESSING_OPTION_DEFINITIONS
}


def normalize_processing_options(raw: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    normalized = dict(DEFAULT_PROCESSING_OPTIONS)
    if not isinstance(raw, dict):
        return normalized

    for key in DEFAULT_PROCESSING_OPTIONS:
        if key in raw:
            normalized[key] = bool(raw[key])
    return normalized


def parse_processing_options(raw: Optional[str]) -> Dict[str, bool]:
    if not raw:
        return dict(DEFAULT_PROCESSING_OPTIONS)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid processing_options JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("processing_options must be a JSON object.")

    return normalize_processing_options(payload)


def build_processing_details_response(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    payload = details if isinstance(details, dict) else {}
    options = normalize_processing_options(payload.get("options"))
    selected_frameworks = payload.get("selected_frameworks") or []

    return {
        "options": [
            {
                "key": option["key"],
                "label": option["label"],
                "enabled": options[option["key"]],
            }
            for option in PROCESSING_OPTION_DEFINITIONS
        ],
        "selected_frameworks": [str(name) for name in selected_frameworks if str(name).strip()],
        "entity_count": int(payload.get("entity_count") or 0),
        "chunks_indexed": int(payload.get("chunks_indexed") or 0),
        "compliance_status": payload.get("compliance_status"),
    }
