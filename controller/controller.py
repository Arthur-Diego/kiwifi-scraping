from service.scraping_service import KiwifyScraper
from service.video_processor_service import VideoProcessor
from facade.extractor_facade import extractor_facade

class Controller:
    def iniciar_extracao(self):
        print("🚀 Iniciando processo via Controller...")

        scraping_service = KiwifyScraper("https://dashboard.kiwify.com/course/premium/163d4f2c-3dab-4a0f-b541-df2165b786c2?mod=2a96a003-8b0e-4638-8f8e-ad34976b3590&sec=7bdf4d05-8d4d-407d-9162-7b17291b5482")  # instância do scraper
        facade = extractor_facade(scraping_service=scraping_service, video_processor_service=VideoProcessor)

        facade.executar_extracao()  # Chama o método da fachada

if __name__ == "__main__":
    controller = Controller()
    controller.iniciar_extracao()