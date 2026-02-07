from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class Aula:
    titulo: str
    link: str


class VideoProcessor:
    """
    Responsável por baixar vídeos (m3u8) e extrair áudio via ffmpeg.

    Mantém comportamento atual:
    - cria uma subpasta por aula
    - salva .mp4 e .wav
    """

    def __init__(self, aulas: Iterable[dict] | Iterable[Aula], pasta_saida: str = "Resultados", headers: Optional[str] = None):
        self.aulas = [a if isinstance(a, Aula) else Aula(titulo=a["titulo"], link=a["link"]) for a in aulas]
        self.pasta_saida = Path(pasta_saida)
        self.headers = headers or (
            "Referer: https://dashboard.kiwify.com\n"
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/141.0.0.0 Safari/537.36\n"
        )
        self.pasta_saida.mkdir(parents=True, exist_ok=True)

    def process_all(self) -> None:
        for idx, aula in enumerate(self.aulas, start=1):
            print(f"\n🚀 Processando: {aula.titulo} -> {aula.link}")

            nome_formatado = self._format_filename(idx, aula.titulo)
            pasta_aula = self.pasta_saida / nome_formatado
            pasta_aula.mkdir(parents=True, exist_ok=True)

            video_file = pasta_aula / f"{nome_formatado}.mp4"
            audio_file = pasta_aula / f"{nome_formatado}.wav"

            self._download_video(aula.link, video_file)
            self._extract_audio(video_file, audio_file)

            print(f"\n✅ Concluído: {aula.titulo}")
            print(f"🎬 Vídeo: {video_file}")
            print(f"🎧 Áudio: {audio_file}")
            print("--------------------------------------------------")

        print("\n🎉 TODOS OS VÍDEOS FORAM PROCESSADOS COM SUCESSO!")

    def _download_video(self, m3u8_url: str, output_file: Path) -> None:
        print(f"\n📥 Baixando vídeo: {m3u8_url}")
        cmd = [
            "ffmpeg",
            "-y",
            "-headers",
            self.headers.replace("\n", "\\r\\n"),
            "-i",
            m3u8_url,
            "-c",
            "copy",
            str(output_file),
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Vídeo salvo como {output_file}")

    def _extract_audio(self, video_file: Path, audio_file: Path) -> None:
        print("🎧 Extraindo áudio do vídeo...")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_file),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-vn",
            "-f",
            "wav",
            str(audio_file),
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Áudio salvo como {audio_file}")

    @staticmethod
    def _format_filename(index: int, titulo: str) -> str:
        numero = str(index).zfill(2)
        titulo_limpo = "".join(c for c in titulo if c.isalnum() or c in (" ", "-", "_")).strip()
        return f"{numero} - {titulo_limpo}"


if __name__ == "__main__":
    aulas = [
        Aula(titulo="Aula 1 - Introdução", link="https://exemplo1.m3u8"),
        Aula(titulo="Aula 2 - Conceitos Avançados", link="https://exemplo2.m3u8"),
    ]
    VideoProcessor(aulas=aulas, pasta_saida="Resultados").process_all()

