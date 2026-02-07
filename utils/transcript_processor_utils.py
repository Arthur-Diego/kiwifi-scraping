from pathlib import Path
from diversos.transcript_service import transcrever_wav

# Defina os formatos de áudio/vídeo aceitos
EXTENSOES = [".wav"]  # pode colocar mais, ex: ".mp4", ".m4a"

def processar_arquivo(arquivo: Path, modelo="small", idioma="pt", device=None):
    txt = arquivo.with_suffix(".txt")
    if txt.exists():
        print(f"⛔ TXT já existe para {arquivo.name}, pulando...")
        return
    try:
        print(f"🎧 Transcrevendo: {arquivo}")
        transcrever_wav(
            caminho_wav=str(arquivo),
            modelo=modelo,
            idioma=idioma,
            saida=None,
            device=device
        )
    except Exception as e:
        print(f"[ERRO] {arquivo}: {e}")

if __name__ == "__main__":
    pasta_base = Path(r"C:\Users\arthu\OneDrive\Área de Trabalho\CURSO_CVD")
    # Procura todos os arquivos com as extensões desejadas
    for ext in EXTENSOES:
        for arquivo in pasta_base.rglob(f"*{ext}"):
            if arquivo.is_file():
                processar_arquivo(arquivo)