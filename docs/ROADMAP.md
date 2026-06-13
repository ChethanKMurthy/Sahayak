# Sahayak roadmap

A living document. Dates are intentions, not promises.

## ✅ Shipped (MVP, 0.1.0)
- Discover → Execute → Track flow end-to-end.
- Deterministic eligibility rules-gate; LLM only explains.
- 7 languages across the whole flow, including voice.
- Web + Flutter clients on a shared knowledge base.
- All-on-Vercel deployment with a stateless backend.

## 🔜 Near-term
- Expand the scheme knowledge base beyond the seed set (more states & central schemes).
- Real OCR/voice providers wired by default (Textract / Bhashini) with graceful fallback.
- Offline-first mobile capture and queued submission.
- Operator (CSC/kiosk) mode with multi-applicant household batching.
- Hardening: rate limits, structured logging, request tracing (in progress).

## 🌅 Mid-term
- Auto-detect scheme deadlines and proactively nudge eligible users.
- Document vault with consent-scoped sharing.
- Status scraping / integration with portals that expose application status.
- Analytics on "benefits unlocked" as the north-star metric.

## 🏔️ Scale (toward 1 crore+ users)
- Cellular architecture, Aurora/managed Postgres, async work queues.
- On-device-first inference to cut cost and protect privacy at scale.
- Regional language quality bar with native reviewers.
- Formal DPDP audit + third-party security review.

See [`infra/README.md`](../infra/README.md) for the current deployment and the path
from MVP to scale.
