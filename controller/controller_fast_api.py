from fastapi import APIRouter
from pydantic import BaseModel
from service.scraping_service import KiwifyScraper
from service.video_processor_service import VideoProcessor
from facade.extractor_facade import extractor_facade

router = APIRouter()

class ExtracaoRequest(BaseModel):
    url: str

@router.post("/iniciar-extracao")
def iniciar_extracao(request: ExtracaoRequest):
    try:
        scraping_service = KiwifyScraper(request.url)
        facade = extractor_facade(
            scraping_service=scraping_service,
            video_processor_service=VideoProcessor
        )
        resultado = facade.executar_extracao()
        return {"status": "sucesso", "resultado": resultado}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
