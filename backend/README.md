# Sahayak — Backend (FastAPI)

The "brain": form-template DSL, the deterministic eligibility **rules-gate**, the
cross-document **consistency engine**, **provenance** + confidence tiers, dependency-chain
+ entitlement-graph **discovery**, PDF generation, voice teach-back, and the session
orchestrator. Every external service (Grok, Textract, Transcribe, Polly, Bhashini, S3)
sits behind an adapter with a **mock**, so it runs with zero credentials.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Python 3.12 recommended
pip install -r requirements.txt
cp .env.example .env          # optional — works fully mocked without it
uvicorn app.main:app --reload # http://localhost:8000  (interactive docs at /docs)
```

## Verify end-to-end

```bash
python smoke_test.py          # runs all demo personas through the full flow + asserts
```

Expected highlights:
- **Ramesh** → qualifies Old-Age Pension (a *surprise* — he came for a ration card)
- **Priya** (with certs) → qualifies Post-Matric Scholarship
- **Priya (missing certs)** → scholarship blocked, **dependency-chain** to income + caste certs
- **Imran** → name mismatch caught by the **consistency engine** before submission

## Layout

```
app/
  engine/      rules-gate, consistency, provenance, discovery, facts  (pure, deterministic)
  services/    swappable adapters (llm/ocr/voice/storage) + mocks
  core/        orchestrator, pii masking, pdf, fill mapper, checklist, teach-back, registry
  schemas/     core domain models + flow request/response models
  api/routes   the HTTP endpoints
  data/        synthetic sample documents (personas)
```

Scheme rules, form templates, and i18n live in **`../shared/`** (the source of truth,
loaded at startup). Add a scheme/form by dropping a JSON file there — no code change.

## Key design rule

The LLM **never decides eligibility**. The deterministic rules-gate
(`app/engine/rules.py`) is the only component that outputs "you qualify"; the LLM only
phrases the explanation, generates voice gap-questions, and maps fields. See
[`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md).

## Switch from mocks to real services

Set in `.env` (local) or Secrets Manager (AWS): `GROK_API_KEY`, `OCR_PROVIDER=textract`,
`VOICE_PROVIDER=bhashini|aws`, AWS creds, `DATABASE_URL` (Postgres). The same code paths
then call the live services.
```
