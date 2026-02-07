from __future__ import annotations

from typing import Protocol, Sequence

from service.scraping_service import KiwifyScraper


class VideoProcessorProtocol(Protocol):
    def __init__(self, aulas: Sequence[dict[str, str]], pasta_saida: str): ...

    def process_all(self) -> None: ...


class ExtractorFacade:
    def __init__(self, scraping_service: KiwifyScraper, video_processor_service: type[VideoProcessorProtocol]):
        self.scraping_service = scraping_service
        self.video_processor_class = video_processor_service
        self.video_processor: VideoProcessorProtocol | None = None

    def executar_extracao(self) -> None:
        print("🔄 Etapa 1: Executando scraping...")
        aulas = self.scraping_service.executar()

        print("🧠 Etapa 2: Configurando VideoProcessor com os dados obtidos...")
        self.video_processor = self.video_processor_class(
            aulas=aulas,
            pasta_saida="Análise da Campanha de Topo e Configuração de Pixel a nível de MCC",
        )

        print("🎬 Etapa 3: Processando vídeos...")
        self.video_processor.process_all()


# Backwards compatibility with existing imports.
extractor_facade = ExtractorFacade

