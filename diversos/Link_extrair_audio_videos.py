import os
import subprocess
import openai
import time
import json

# ================================
# CONFIGURAÇÕES DO USUÁRIO
# ================================
M3U8_URL = "https://d3pjuhbfoxhm7c.cloudfront.net/ofutO348rDwCi2K/2025/01/15/9de4be27-eb72-45ab-b990-30ea9e7bffa8/9de4be27-eb72-45ab-b990-30ea9e7bffa8-720p.m3u8"
VIDEO_FILE = "video.mp4"
AUDIO_FILE = "audio.wav"
TRANSCRIPTION_FILE = "transcription.txt"
SRT_FILE = "subtitles.srt"

# Modelo da OpenAI
OPENAI_MODEL = "whisper-1"

# Headers necessários (adicione se for preciso Referer ou Cookie)
HEADERS = """Referer: https://dashboard.kiwify.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
"""

# ================================
# 1. Baixar vídeo via ffmpeg
# ================================
def download_video(m3u8_url, output_file):
    print("📥 Baixando o vídeo com ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-headers", HEADERS.replace("\n", "\\r\\n"),
        "-i", m3u8_url,
        "-c", "copy",
        output_file
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Vídeo salvo como {output_file}")

# ================================
# 2. Extrair áudio com ffmpeg
# ================================
def extract_audio(video_file, audio_file):
    print("🎧 Extraindo áudio...")
    cmd = [
        "ffmpeg", "-y",
        "-i", video_file,
        "-ac", "1",  # mono
        "-ar", "16000",  # 16 kHz
        "-vn",
        "-f", "wav",
        audio_file
    ]
    subprocess.run(cmd, check=True)
    print(f"✅ Áudio extraído: {audio_file}")

# ================================
# 3. Enviar áudio para API da OpenAI
# ================================
def transcribe_audio(audio_file):
    print("🧠 Transcrevendo com OpenAI...")
    with open(audio_file, "rb") as audio:
        response = openai.Audio.transcribe(
            model=OPENAI_MODEL,
            file=audio,
            response_format="verbose_json",  # retorna os segmentos com timestamps
            temperature=0
        )
    return response

# ================================
# 4. Salvar transcrição em TXT
# ================================
def save_txt(transcription, txt_file):
    print("💾 Salvando texto completo...")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(transcription["text"])
    print(f"✅ Transcrição salva em {txt_file}")

# ================================
# 5. Gerar SRT
# ================================
def save_srt(segments, srt_file):
    print("💾 Gerando legendas SRT...")
    def format_timestamp(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    with open(srt_file, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, start=1):
            start = format_timestamp(seg["start"])
            end = format_timestamp(seg["end"])
            text = seg["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")
    print(f"✅ Legendas salvas em {srt_file}")

# ================================
# EXECUÇÃO PRINCIPAL
# ================================
if __name__ == "__main__":
    if not os.path.exists(VIDEO_FILE):
        download_video(M3U8_URL, VIDEO_FILE)
    else:
        print(f"⚠️ {VIDEO_FILE} já existe, pulando download.")

    extract_audio(VIDEO_FILE, AUDIO_FILE)
    transcription = transcribe_audio(AUDIO_FILE)
    save_txt(transcription, TRANSCRIPTION_FILE)
    save_srt(transcription["segments"], SRT_FILE)

    print("\n🎉 PROCESSO CONCLUÍDO COM SUCESSO!")
    print(f"📄 Arquivo TXT: {TRANSCRIPTION_FILE}")
    print(f"💬 Arquivo SRT: {SRT_FILE}")
    print("✅ Tudo pronto para você usar ou importar em editores de vídeo.")