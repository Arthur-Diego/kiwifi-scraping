from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.domain.campaigns.entities import Campaign, CampaignEvent, CampaignEventKind


class JsonCampaignRepository:
    def __init__(self, base_dir: Path = Path("data/chat_history")):
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def list_campaigns(self) -> list[str]:
        return sorted(file.stem for file in self._base_dir.glob("*.json"))

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        file_path = self._campaign_file(campaign_id)
        if not file_path.exists():
            return None
        return Campaign(campaign_id=campaign_id, name=campaign_id)

    def create_campaign(self, campaign_id: str, name: str | None = None) -> Campaign:
        file_path = self._campaign_file(campaign_id)
        if not file_path.exists():
            file_path.write_text("[]", encoding="utf-8")
        return Campaign(campaign_id=campaign_id, name=name or campaign_id)

    def list_events(self, campaign_id: str) -> list[CampaignEvent]:
        file_path = self._campaign_file(campaign_id)
        if not file_path.exists():
            return []

        payload = json.loads(file_path.read_text(encoding="utf-8"))
        events: list[CampaignEvent] = []
        for item in payload:
            kind_name = str(item.get("kind") or "NOTE").upper()
            kind = CampaignEventKind(kind_name) if kind_name in CampaignEventKind.__members__ else CampaignEventKind.NOTE
            timestamp_raw = item.get("timestamp")
            timestamp = datetime.fromisoformat(timestamp_raw) if timestamp_raw else datetime.utcnow()
            events.append(
                CampaignEvent(
                    campaign_id=campaign_id,
                    kind=kind,
                    payload=item.get("payload") or {"text": item.get("text", "")},
                    tags=item.get("tags") or [],
                    timestamp=timestamp,
                )
            )
        return events

    def append_event(self, event: CampaignEvent) -> None:
        file_path = self._campaign_file(event.campaign_id)
        if not file_path.exists():
            self.create_campaign(event.campaign_id)

        payload = json.loads(file_path.read_text(encoding="utf-8"))
        payload.append(
            {
                "timestamp": event.timestamp.isoformat(),
                "kind": event.kind.value,
                "payload": event.payload,
                "tags": event.tags,
                "sender": "assistant" if event.kind != CampaignEventKind.NOTE else "user",
                "text": event.payload.get("text", ""),
            }
        )
        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _campaign_file(self, campaign_id: str) -> Path:
        return self._base_dir / f"{campaign_id}.json"
