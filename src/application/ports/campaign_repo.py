from __future__ import annotations

from typing import Protocol

from src.domain.campaigns.entities import Campaign, CampaignEvent


class CampaignRepositoryPort(Protocol):
    def list_campaigns(self) -> list[str]:
        ...

    def get_campaign(self, campaign_id: str) -> Campaign | None:
        ...

    def create_campaign(self, campaign_id: str, name: str | None = None) -> Campaign:
        ...

    def list_events(self, campaign_id: str) -> list[CampaignEvent]:
        ...

    def append_event(self, event: CampaignEvent) -> None:
        ...
