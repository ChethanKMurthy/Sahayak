# Security Policy

## Reporting a vulnerability

Please report security issues privately — **do not** open a public issue.

- Email: security@sahayak.app (or open a private security advisory on GitHub).
- Include reproduction steps and impact. We aim to acknowledge within 72 hours.

Please do not include real Aadhaar numbers or other personal data in reports; use
synthetic values.

## Supported versions

The project is pre-1.0; only the latest `master` is supported with fixes.

## Data handling principles

Sahayak is built to be safe with sensitive identity data under India's DPDP framework:

- **Minimisation** — documents persist as metadata only; the full Aadhaar number is
  never written to the database.
- **On-device first** — OCR runs on-device where possible; cloud providers are opt-in.
- **Append-only audit log** — every read/ask/consent/output is recorded as DPDP evidence.
- **Consent before output** — the filled form is read back to the user and confirmed
  before any submittable artifact is produced.
- **No secrets in the repo** — keys are injected via environment / Secrets Manager.

## Scope

In scope: the backend API, web app, mobile app, and infrastructure templates in this
repository. Third-party providers (Groq, AWS, Bhashini) follow their own policies.
