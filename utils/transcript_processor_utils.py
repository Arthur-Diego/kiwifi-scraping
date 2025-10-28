from pathlib import Path
from diversos.transcript_service import transcrever_wav

def processar_pasta_recursivamente(raiz_pasta: Path, modelo="small", idioma="pt", device=None):
    raiz_pasta = raiz_pasta.resolve()
    print(f"[+] Iniciando varredura completa em: {raiz_pasta}")
    encontrados = list(raiz_pasta.rglob("*.wav"))

    if not encontrados:
        print("⚠ Nenhum arquivo .wav encontrado. Verifique o caminho ou a extensão.")
        return

    for wav in encontrados:
        print(f"🎧 Encontrado: {wav}")
        try:
            transcrever_wav(
                caminho_wav=str(wav),
                modelo=modelo,
                idioma=idioma,
                saida=None,   # gera o .txt no mesmo diretório do .wav
                device=device
            )
        except Exception as e:
            print(f"[ERRO] {wav}: {e}")

if __name__ == "__main__":
    # Este arquivo fica em .../Scraping/utils/transcript_processor_utils.py
    # Subimos UM nível (parents[1]) para chegar em .../Scraping/
    projeto_root = Path(__file__).resolve().parents[1]

    # Agora apontamos para controller/Resultados sob a raiz do projeto
    pasta_resultados = projeto_root / "controller" / "Resultados"

    processar_pasta_recursivamente(
        raiz_pasta=pasta_resultados,
        modelo="small",
        idioma="pt",
        device=None
    )
