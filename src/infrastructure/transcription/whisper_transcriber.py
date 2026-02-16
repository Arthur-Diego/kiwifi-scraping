from __future__ import annotations

import whisper


class WhisperTranscriber:
    """Infrastructure-only wrapper for OpenAI Whisper local transcription."""

    def transcribe_file(self, audio_path: str, *, model_name: str = "small", language: str | None = None) -> str:
        model = whisper.load_model(model_name)
        result = model.transcribe(audio=audio_path, language=language, task="transcribe")
        return str(result.get("text", "")).strip()
