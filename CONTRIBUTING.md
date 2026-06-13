# Contributing to Sahayak

Thanks for helping make government benefits easier to claim. This guide gets you productive fast.

## Repository layout

| Path | What |
|---|---|
| `backend/` | Python 3.12 FastAPI brain (rules-gate, OCR/voice/LLM adapters) |
| `web/` | Next.js 14 web app |
| `mobile/` | Flutter Android app |
| `shared/` | Scheme KB + form DSL + 7-language i18n (single source of truth) |
| `infra/` | Terraform (AWS) |

## Local setup

### Backend
```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # http://localhost:8000
python smoke_test.py               # full end-to-end check
```
Everything runs on deterministic mocks with **zero API keys**. Set `GROK_API_KEY`,
`OCR_PROVIDER`, `VOICE_PROVIDER` etc. to go live.

### Web
```bash
cd web && npm install && npm run dev    # http://localhost:3000 (proxies /api → :8000)
```

### Mobile
```bash
cd mobile && flutter run
```

Or use the shortcuts in the [`Makefile`](Makefile): `make install`, `make backend`, `make web`, `make test`, `make smoke`.

## Tests & style
- `make test` runs backend unit tests; `make smoke` runs the full flow.
- `make fmt` formats (black + ruff + prettier); `make lint` lints.
- Install hooks once: `pre-commit install`.

## The one rule that never bends
The LLM **never** decides eligibility. Only the deterministic rules-gate
(`backend/app/engine/rules.py`) may output "you qualify." The LLM explains, asks
gap questions, and maps fields — nothing more.

## Pull requests
Branch from `master`, keep PRs focused, fill in the PR template, and make sure no
secrets or real PII (e.g. full Aadhaar numbers) are committed.
