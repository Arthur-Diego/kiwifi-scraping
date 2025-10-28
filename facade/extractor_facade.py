

from service.scraping_service import KiwifyScraper


class extractor_facade:
    def __init__(self, scraping_service: KiwifyScraper, video_processor_service):
        self.scraping_service = scraping_service
        self.video_processor_class = video_processor_service
        self.video_processor = None

    def executar_extracao(self):
        print("🔄 Etapa 1: Executando scraping...")
        aulas = self.scraping_service.executar()

        print("🧠 Etapa 2: Configurando VideoProcessor com os dados obtidos...")
        self.video_processor = self.video_processor_class(aulas=aulas, pasta_saida="2 - Imersões Online de Aprimoramento")

        print("🎬 Etapa 3: Processando vídeos...")
        self.video_processor.process_all()
