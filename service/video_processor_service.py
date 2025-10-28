import os
import subprocess


class VideoProcessor:
    """
    Classe responsável por baixar vídeos, extrair áudio e salvar arquivos com nome formatado por título e ordem.
    """

    def __init__(self, aulas, pasta_saida="Resultados", headers=None):
        """
        aulas: lista de dicionários no formato:
            [
                {"titulo": "Aula 1 - Introdução", "link": "https://exemplo1.m3u8"},
                {"titulo": "Aula 2 - Conceitos", "link": "https://exemplo2.m3u8"},
            ]
        """
        self.aulas = aulas
        self.pasta_saida = pasta_saida
        self.headers = headers or (
            """Referer: https://dashboard.kiwify.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
"""
        )
        os.makedirs(self.pasta_saida, exist_ok=True)

    # ================================
    # Métodos PRIVADOS
    # ================================
    def __download_video(self, m3u8_url, output_file):
        print(f"\n📥 Baixando vídeo: {m3u8_url}")
        cmd = [
            "ffmpeg", "-y",
            "-headers", self.headers.replace("\n", "\\r\\n"),
            "-i", m3u8_url,
            "-c", "copy",
            output_file
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Vídeo salvo como {output_file}")

    def __extract_audio(self, video_file, audio_file):
        print("🎧 Extraindo áudio do vídeo...")
        cmd = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-ac", "1",
            "-ar", "16000",
            "-vn",
            "-f", "wav",
            audio_file
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Áudio salvo como {audio_file}")

    def __format_filename(self, index, titulo):
        """
        Gera um nome de arquivo padronizado com número sequencial e título limpo.
        """
        numero = str(index).zfill(2)  # deixa com dois dígitos: 01, 02...
        titulo_limpo = "".join(c for c in titulo if c.isalnum() or c in (' ', '-', '_')).strip()
        return f"{numero} - {titulo_limpo}"

    # ================================
    # Métodos PÚBLICOS
    # ================================
    def process_all(self):
        """
        Executa todo o processo para todos os vídeos da lista.
        """
        for idx, aula in enumerate(self.aulas, start=1):
            titulo = aula['titulo']
            link = aula['link']
            print(f"\n🚀 Processando: {titulo} -> {link}")

            nome_formatado = self.__format_filename(idx, titulo)
            pasta_video = os.path.join(self.pasta_saida, nome_formatado)
            os.makedirs(pasta_video, exist_ok=True)

            video_file = os.path.join(pasta_video, f"{nome_formatado}.mp4")
            audio_file = os.path.join(pasta_video, f"{nome_formatado}.wav")

            self.__download_video(link, video_file)
            self.__extract_audio(video_file, audio_file)

            print(f"\n✅ Concluído: {titulo}")
            print(f"🎬 Vídeo: {video_file}")
            print(f"🎧 Áudio: {audio_file}")
            print("--------------------------------------------------")

        print("\n🎉 TODOS OS VÍDEOS FORAM PROCESSADOS COM SUCESSO!")


# ================================
# Exemplo de uso
# ================================
if __name__ == "__main__":
    AULAS = [
        {"titulo": "Aula 1 - Introdução", "link": "https://exemplo1.m3u8"},
        {"titulo": "Aula 2 - Conceitos Avançados", "link": "https://exemplo2.m3u8"},
    ]

    processor = VideoProcessor(aulas=AULAS, pasta_saida="Resultados")
    processor.process_all()
