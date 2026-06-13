"""Validate that the real provider keys in .env actually work.

Run:  python validate_keys.py
Tests only the providers you've configured; everything else is reported as 'mock'.
Makes tiny live calls (a few tokens / a 1-line TTS / an STS identity check).
"""
import asyncio
import base64

from app.config import settings


def line(name, status, detail=""):
    mark = {"ok": "✅", "fail": "❌", "skip": "•"}.get(status, "?")
    print(f"{mark}  {name:<22} {detail}")


async def check_grok():
    if not settings.grok_api_key:
        return line("Grok (xAI)", "skip", "no GROK_API_KEY — using mock")
    import httpx
    try:
        async with httpx.AsyncClient(base_url=settings.grok_base_url, timeout=20,
                                     headers={"Authorization": f"Bearer {settings.grok_api_key}"}) as c:
            r = await c.post("/chat/completions", json={
                "model": settings.grok_model,
                "messages": [{"role": "user", "content": "Reply with the single word: ready"}],
                "max_tokens": 5,
            })
            r.raise_for_status()
            txt = r.json()["choices"][0]["message"]["content"].strip()
            line("Grok (xAI)", "ok", f'model={settings.grok_model}, replied "{txt[:20]}"')
    except Exception as e:
        line("Grok (xAI)", "fail", str(e)[:120])


def check_aws():
    if not settings.aws_access_key_id:
        return line("AWS creds", "skip", "no AWS_ACCESS_KEY_ID — Textract/Polly use mock")
    try:
        import boto3
        sts = boto3.client("sts", region_name=settings.aws_region,
                           aws_access_key_id=settings.aws_access_key_id,
                           aws_secret_access_key=settings.aws_secret_access_key)
        ident = sts.get_caller_identity()
        line("AWS creds", "ok", f"account {ident['Account']}, region {settings.aws_region}")
    except Exception as e:
        return line("AWS creds", "fail", str(e)[:120])

    # Polly (TTS) — synthesize one short clip.
    try:
        import boto3
        polly = boto3.client("polly", region_name=settings.aws_region,
                             aws_access_key_id=settings.aws_access_key_id,
                             aws_secret_access_key=settings.aws_secret_access_key)
        out = polly.synthesize_speech(Text="नमस्ते", OutputFormat="mp3", VoiceId="Aditi",
                                      LanguageCode="hi-IN")
        n = len(out["AudioStream"].read())
        line("AWS Polly (TTS)", "ok", f"{n} bytes of audio")
    except Exception as e:
        line("AWS Polly (TTS)", "fail", str(e)[:120])

    # Textract — needs a real image; just confirm the client/permission resolves.
    try:
        import boto3
        tx = boto3.client("textract", region_name=settings.aws_region,
                          aws_access_key_id=settings.aws_access_key_id,
                          aws_secret_access_key=settings.aws_secret_access_key)
        # 1x1 png — Textract rejects the content, but a 4xx proves auth+permission work.
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
        try:
            tx.detect_document_text(Document={"Bytes": png})
            line("AWS Textract (OCR)", "ok", "call accepted")
        except tx.exceptions.ClientError as ce:
            code = ce.response["Error"]["Code"]
            if code in ("UnsupportedDocumentException", "BadDocumentException", "InvalidParameterException"):
                line("AWS Textract (OCR)", "ok", "auth+permission OK (test image rejected as expected)")
            else:
                line("AWS Textract (OCR)", "fail", code)
    except Exception as e:
        line("AWS Textract (OCR)", "fail", str(e)[:120])


async def check_bhashini():
    if not (settings.bhashini_api_key and settings.bhashini_user_id):
        return line("Bhashini (voice)", "skip", "no BHASHINI keys — using AWS/mock")
    import httpx
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://dhruva-api.bhashini.gov.in/services/inference/pipeline",
                headers={"Authorization": settings.bhashini_api_key, "userID": settings.bhashini_user_id},
                json={"pipelineTasks": [{"taskType": "tts",
                       "config": {"language": {"sourceLanguage": "hi"}}}],
                      "inputData": {"input": [{"source": "नमस्ते"}]}})
            if r.status_code < 400:
                line("Bhashini (voice)", "ok", "pipeline responded")
            else:
                line("Bhashini (voice)", "fail", f"{r.status_code}: {r.text[:80]}")
    except Exception as e:
        line("Bhashini (voice)", "fail", str(e)[:120])


async def main():
    print("\nSahayak — live provider key validation\n" + "-" * 42)
    line("Selected OCR provider", "ok" if settings.ocr_provider != "mock" else "skip", settings.ocr_provider)
    line("Selected voice provider", "ok" if settings.voice_provider != "mock" else "skip", settings.voice_provider)
    print("-" * 42)
    await check_grok()
    check_aws()
    await check_bhashini()
    print("-" * 42)
    print("Tip: set OCR_PROVIDER=textract and VOICE_PROVIDER=aws|bhashini in .env to use them.\n")


if __name__ == "__main__":
    asyncio.run(main())
