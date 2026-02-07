import os
import subprocess


# ================================
# CONFIGURAÇÕES DO USUÁRIO
# ================================
M3U8_URLS = [
    "HTTP::TESTE"]  # Adicione várias URLs aqui
PASTA_SAIDA = "Resultados"

# Modelo da OpenAI
OPENAI_MODEL = "whisper-1"
# Headers necessários
HEADERS = """Referer: https://dashboard.kiwify.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
"""

# ================================
# Funções Auxiliares
# ================================
def download_video(m3u8_url, output_file):
    print(f"\n📥 Baixando vídeo: {m3u8_url}")
    cmd = [
        "ffmpeg", "-y",
        "-headers", HEADERS.replace("\n", "\\r\\n"),
        "-i", m3u8_url,
        "-c", "copy",
        output_file
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Vídeo salvo como {output_file}")

def extract_audio(video_file, audio_file):
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

#def transcribe_audio(audio_file):
#     print("🧠 Transcrevendo com OpenAI...")
#     with open(audio_file, "rb") as audio:
#         response = openai.Audio.transcribe(
#             model=OPENAI_MODEL,
#             file=audio,
#             response_format="verbose_json",
#             temperature=0
#         )
# #    return response

def save_txt(transcription, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(transcription["text"])
    print(f"✅ Texto salvo em {path}")

def save_srt(segments, path):
    def format_timestamp(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    print(f"✅ Legendas salvas em {path}")

# ================================
# EXECUÇÃO PRINCIPAL
# ================================
if __name__ == "__main__":
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    for idx, url in enumerate(M3U8_URLS, start=1):
        print(f"\n🚀 Processando vídeo {idx}/{len(M3U8_URLS)}")
        nome_base = f"video_{idx}"
        pasta_video = os.path.join(PASTA_SAIDA, nome_base)
        os.makedirs(pasta_video, exist_ok=True)

        video_file = os.path.join(pasta_video, f"{nome_base}.mp4")
        audio_file = os.path.join(pasta_video, f"{nome_base}.wav")
        txt_file = os.path.join(pasta_video, f"{nome_base}.txt")
        srt_file = os.path.join(pasta_video, f"{nome_base}.srt")

        download_video(url, video_file)
        extract_audio(video_file, audio_file)
        # transcription = transcribe_audio(audio_file)
        # save_txt(transcription, txt_file)
        # save_srt(transcription["segments"], srt_file)

        print(f"\n✅ Vídeo {idx} concluído com sucesso!")
        print(f"📄 TXT: {txt_file}")
        print(f"💬 SRT: {srt_file}")
        print("--------------------------------------------------")

    print("\n🎉 TODOS OS VÍDEOS FORAM PROCESSADOS COM SUCESSO!")