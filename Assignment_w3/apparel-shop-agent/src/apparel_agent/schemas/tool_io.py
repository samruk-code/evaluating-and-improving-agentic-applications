from __future__ import annotations

from typing import Any

JsonDict = dict[str, Any]


def success_response(**kwargs: Any) -> JsonDict:
    return {"success": True, **kwargs}


def failure_response(reason: str, **kwargs: Any) -> JsonDict:
    return {"success": False, "reason": reason, **kwargs}

