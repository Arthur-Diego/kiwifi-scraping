from fastapi import FastAPI
from controller.controller_fast_api import router as controller_router

app = FastAPI(
    title="API de Extração Kiwify",
    description="Inicia processo de scraping e extração de vídeos",
    version="1.0.0"
)

# Inclui rotas do controller
app.include_router(controller_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "API ativa! Acesse /docs para ver a documentação Swagger"}
