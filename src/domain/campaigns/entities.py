from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CampaignEventKind(str, Enum):
    METRICS = "METRICS"
    DECISION = "DECISION"
    NOTE = "NOTE"
    RESULT = "RESULT"


@dataclass(frozen=True)
class Campaign:
    campaign_id: str
    name: str
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class CampaignEvent:
    campaign_id: str
    kind: CampaignEventKind
    payload: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
