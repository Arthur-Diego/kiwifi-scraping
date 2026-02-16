from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.application.ports.campaign_repo import CampaignRepositoryPort
from src.application.ports.logger_port import LoggerPort
from src.domain.campaigns.entities import CampaignEvent, CampaignEventKind


@dataclass(frozen=True)
class RecordCampaignEventInput:
    campaign_id: str
    kind: CampaignEventKind
    payload: dict[str, Any]
    tags: list[str]


class RecordCampaignEventUseCase:
    def __init__(self, *, campaign_repo: CampaignRepositoryPort, logger: LoggerPort):
        self._campaign_repo = campaign_repo
        self._logger = logger

    def execute(self, data: RecordCampaignEventInput) -> None:
        if self._campaign_repo.get_campaign(data.campaign_id) is None:
            self._campaign_repo.create_campaign(campaign_id=data.campaign_id, name=data.campaign_id)

        self._campaign_repo.append_event(
            CampaignEvent(
                campaign_id=data.campaign_id,
                kind=data.kind,
                payload=data.payload,
                tags=data.tags,
            )
        )
        self._logger.info(f"Campaign event recorded for '{data.campaign_id}' ({data.kind}).")
