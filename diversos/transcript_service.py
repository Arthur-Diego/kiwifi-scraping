import argparse
import os
import sys
import whisper
import torch

def transcrever_wav(caminho_wav: str, modelo: str = "small", idioma: str = None, saida: str = None, device: str = None):
    """
    Transcreve um arquivo .wav usando Whisper local.
    - caminho_wav: caminho do arquivo WAV
    - modelo: tiny | base | small | medium | large (quanto maior, melhor e mais lento)
    - idioma: ex. 'pt' para forçar português; se None, o Whisper detecta
    - saida: caminho do .txt de saída; se None, usa mesmo nome do áudio
    - device: 'cpu' ou 'cuda' (auto se None)
    """
    if not os.path.isfile(caminho_wav):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_wav}")

    # preferências p/ CPU
    # Se device não for especificado pelo usuário, detecta automaticamente
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"[+] Dispositivo detectado: {device.upper()}")

    # preferências p/ CPU
    kwargs = {}
    if device == "cuda":
        kwargs["fp16"] = True

    # carrega modelo
    print(f"[+] Carregando modelo Whisper: {modelo} ...")
    model = whisper.load_model(modelo, device=device)

    # transcreve
    print(f"[+] Transcrevendo: {caminho_wav}")
    result = model.transcribe(
        audio=caminho_wav,
        language=idioma,    # None = auto-detecção
        task="transcribe",  # ou "translate" p/ traduzir p/ inglês
        **kwargs
    )

    texto = result.get("text", "").strip()

    # salva saída
    if saida is None:
        base, _ = os.path.splitext(caminho_wav)
        saida = base + ".txt"

    with open(saida, "w", encoding="utf-8") as f:
        f.write(texto + "\n")

    print(f"[✓] Transcrição salva em: {saida}")
    return texto

def main():
    parser = argparse.ArgumentParser(description="Transcreve um arquivo WAV para texto usando Whisper local.")
    parser.add_argument("wav", help="Caminho do arquivo .wav")
    parser.add_argument("--modelo", default="small", help="tiny, base, small, medium, large (padrão: small)")
    parser.add_argument("--idioma", default=None, help="Força um idioma (ex.: pt, en). Padrão: auto-detecção")
    parser.add_argument("--saida", default=None, help="Caminho do arquivo .txt de saída")
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None, help="Força CPU ou CUDA (GPU)")
    args = parser.parse_args()

    try:
        transcrever_wav(args.wav, modelo=args.modelo, idioma=args.idioma, saida=args.saida, device=args.device)
    except Exception as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
