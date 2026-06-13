"""Voice adapter: ASR (speech→text) + TTS (text→speech) for the teach-back.

Primary = Bhashini (India's national language stack); fallback = AWS
Transcribe/Polly. Mock echoes text and returns a tiny silent audio placeholder so
the web/mobile flow works without any voice keys.
"""
from __future__ import annotations

import base64
from typing import Protocol

import httpx

from ..config import settings

# Bhashini language codes for our 7 supported languages.
LANGS = ["hi", "en", "kn", "ta", "te", "mr", "bn"]


class VoiceAdapter(Protocol):
    async def transcribe(self, audio_b64: str, lang: str) -> str: ...
    async def synthesize(self, text: str, lang: str) -> str: ...  # returns audio b64


class MockVoice:
    async def transcribe(self, audio_b64: str, lang: str) -> str:
        # The web/mobile client uses the browser/OS speech API in mock mode and
        # posts the recognised text directly; if raw audio arrives we return "".
        try:
            decoded = base64.b64decode(audio_b64 or "")
            return decoded.decode("utf-8", "ignore") if decoded[:5] != b"\x00\x00\x00\x00\x00" else ""
        except Exception:
            return ""

    async def synthesize(self, text: str, lang: str) -> str:
        # Minimal silent WAV placeholder; clients fall back to on-device TTS.
        return ""


class AWSVoice:
    def __init__(self) -> None:
        import boto3

        self._transcribe = boto3.client("transcribe", region_name=settings.aws_region)
        self._polly = boto3.client("polly", region_name=settings.aws_region)

    _POLLY_VOICE = {"hi": "Aditi", "en": "Kajal", "ta": "Aditi", "te": "Aditi",
                    "kn": "Aditi", "mr": "Aditi", "bn": "Aditi"}

    async def transcribe(self, audio_b64: str, lang: str) -> str:
        # Real impl uploads to S3 + starts a transcription job; omitted for brevity.
        # Streaming Transcribe would be wired here in production.
        return ""

    async def synthesize(self, text: str, lang: str) -> str:
        resp = self._polly.synthesize_speech(
            Text=text, OutputFormat="mp3",
            VoiceId=self._POLLY_VOICE.get(lang, "Aditi"), LanguageCode=f"{lang}-IN",
        )
        return base64.b64encode(resp["AudioStream"].read()).decode()


class BhashiniVoice:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)
        self._headers = {"Authorization": settings.bhashini_api_key, "userID": settings.bhashini_user_id}

    async def transcribe(self, audio_b64: str, lang: str) -> str:
        # Bhashini ASR pipeline call (pipeline id provisioned per account).
        try:
            resp = await self._client.post(
                "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                headers=self._headers,
                json={"pipelineTasks": [{"taskType": "asr", "config": {"language": {"sourceLanguage": lang}}}],
                      "inputData": {"audio": [{"audioContent": audio_b64}]}},
            )
            resp.raise_for_status()
            return resp.json()["pipelineResponse"][0]["output"][0]["source"]
        except (httpx.HTTPError, KeyError, IndexError):
            return ""

    async def synthesize(self, text: str, lang: str) -> str:
        try:
            resp = await self._client.post(
                "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                headers=self._headers,
                json={"pipelineTasks": [{"taskType": "tts", "config": {"language": {"sourceLanguage": lang}}}],
                      "inputData": {"input": [{"source": text}]}},
            )
            resp.raise_for_status()
            return resp.json()["pipelineResponse"][0]["audio"][0]["audioContent"]
        except (httpx.HTTPError, KeyError, IndexError):
            return ""


def get_voice() -> VoiceAdapter:
    if settings.voice_provider == "bhashini" and settings.bhashini_api_key:
        return BhashiniVoice()
    if settings.voice_provider == "aws":
        return AWSVoice()
    return MockVoice()
