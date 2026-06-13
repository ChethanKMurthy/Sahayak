# Sahayak — Scaling to 1 Crore+ (10M+) Users

This is the engineering+operations plan for taking the MVP architecture in
[`ARCHITECTURE.md`](ARCHITECTURE.md) to nationwide scale. It is written to be honest about cost,
correctness, and the parts that are operational rather than technical.

---

## 0. What "1cr+ users" actually means here

"Users" for Sahayak is not "concurrent API calls." The load profile is:

- **Bursty, assisted, sessional.** A session is minutes long (capture → fill → consent) and produces
  a handful of heavy calls (OCR, a few LLM calls, one PDF). Most users transact a few times a year,
  often via a CSC operator handling many citizens sequentially.
- **Heavily regional + multilingual.** Load correlates with state, language, and government scheme
  cycles (scholarship season, pension drives).
- **Correctness-critical, latency-tolerant-ish.** A wrong eligibility answer is far worse than a 3s
  wait. This shapes every trade-off below.

### Capacity targets (planning envelope)

| Metric | MVP | 1cr+ target |
|---|---|---|
| Registered users | 10³–10⁴ | 10⁷+ |
| Active sessions / day | ~10² | 1–3 × 10⁶ |
| Peak concurrent sessions | ~10 | ~50k |
| Documents OCR'd / day | ~10³ | ~10⁷ |
| LLM calls / day | ~10³ | ~2 × 10⁷ |
| PDFs / day | ~10² | ~10⁶ |
| p95 end-to-end session | < 90s | < 90s (hold the line) |

These numbers drive the cost model in §7.

---

## 1. Scaling stages (don't over-build early)

| Stage | Users | Shape | Key moves |
|---|---|---|---|
| **0 — MVP** | <10k | Single FastAPI on EC2/Lambda, one RDS, mocks→real keys | Ship; instrument everything |
| **1 — Regional pilot** | 100k | Horizontal API, read replicas, S3 lifecycle, CDN, Redis cache | Stateless API, autoscaling group |
| **2 — Multi-state** | 1M | Service decomposition, queue-based heavy work, on-device OCR default | Decouple OCR/LLM/PDF into workers |
| **3 — National** | 10M+ | Cell-based per-region deploys, model tiering, regional data residency | Sharding, multi-region, cost engineering |

The MVP is deliberately a modular monolith so that Stage-2 decomposition is a refactor, not a rewrite
(see §3).

---

## 2. Compute & request path

**Stateless API tier.** The FastAPI app holds no session state in memory — working state lives in
Postgres/Redis — so it scales horizontally behind an ALB. On AWS:

- Stage 0–1: ECS Fargate or an EC2 Auto Scaling Group; target-tracking on CPU + request count.
- Stage 2–3: same, but **cell-based** — independent stacks per region (e.g. North/South/East/West)
  so a bad deploy or a scholarship-season spike in one region cannot take down the country. Route by
  user's state at the edge.

**Heavy work goes async.** OCR (cloud fallback), LLM extraction, and PDF generation are pulled off
the request path into a queue (SQS) consumed by autoscaling workers. The mobile/web client opened a
session and polls/streams status. This:
- smooths bursts (queue absorbs the scholarship-season spike),
- lets OCR/LLM/PDF scale independently on their own cost curves,
- makes retries and idempotency first-class.

**Edge.** CloudFront in front of web static assets + the public scheme catalog (cacheable, same for
everyone). API behind it for TLS termination + WAF.

---

## 3. Service decomposition (Stage 2)

The MVP modules map 1:1 to future services — they already talk through interfaces:

| MVP module | Becomes | Scaling reason |
|---|---|---|
| Extraction service | **OCR/Extraction workers** | GPU/throughput-bound, bursty; isolate cost |
| Eligibility engine | **Rules service** (stateless, cache-heavy) | Pure CPU, trivially horizontal, must stay deterministic |
| Form-fill / DSL | **Fill service** | Tied to template store; versioned releases |
| PDF generator | **PDF workers** | CPU+memory spikes; isolate |
| Voice (ASR/TTS) | **Voice gateway** | Vendor fan-out (Bhashini/AWS), per-language routing |
| Consistency engine | stays in Rules service | Cheap, runs with eligibility |

Communication: synchronous for cheap/fast (rules, consistency), **queue for heavy** (OCR/LLM/PDF).

---

## 4. Data tier at scale

- **Postgres (RDS → Aurora)**: vertical first, then **read replicas** for the heavy reads (scheme
  catalog, form templates, user history). Aurora at Stage 2 for storage autoscaling + fast replicas.
- **Sharding key = applicant/household id**, aligned to region cells. Reference data (schemes,
  templates) is small and replicated to every cell.
- **Ephemeral session + PII** in **Redis (ElastiCache)** with hard TTLs — reinforces "ephemeral by
  default; Aadhaar never persisted." Working document text expires in minutes.
- **S3** for transient document images (lifecycle expiry, e.g. 24–72h) and generated PDFs (retained
  per user policy, encrypted with KMS). Aadhaar full number is never stored anywhere.
- **Search/retrieval** for the eligibility knowledge base: start with Postgres + pgvector for scheme
  retrieval; move to OpenSearch only if KB grows past what pgvector serves comfortably.

---

## 5. The AI cost curve (the real scaling problem)

LLM + OCR + voice dominate variable cost. Strategy, in priority order:

1. **Do it on-device.** ML Kit OCR and on-device ASR/TTS where the device allows → marginal cost ~0
   and the privacy story holds. Cloud OCR/voice become *fallbacks*, not the default. This single lever
   is the difference between viable and not at 10M users.
2. **Model tiering for the LLM.** Most extraction/mapping is routine → route to a small/cheap model;
   escalate to Grok's larger model only on low confidence or ambiguity. A classifier picks the tier.
3. **Cache aggressively.** Identical form templates, scheme explanations, and prompt prefixes are
   cached (prompt caching + a semantic cache for repeated explanation text). Eligibility *results*
   are pure functions of facts → memoizable.
4. **Batch + queue.** Off-peak and bulk operator workloads batch through workers at lower priority.
5. **Keep the rules-gate off the LLM entirely.** Eligibility is free, deterministic CPU — never a
   token. This is both a correctness and a cost decision.

**Voice at scale**: route per language to the cheapest competent provider (Bhashini where strong,
AWS Polly/Transcribe elsewhere); cache TTS for static prompts; only the dynamic teach-back of a
specific filled form is synthesized fresh.

---

## 6. Correctness & trust at scale (non-negotiable)

- **Deterministic rules-gate stays the sole eligibility authority** regardless of scale. It is
  versioned, unit-tested per scheme, and changes go through review like code.
- **Form templates and scheme rules are versioned, staged, and canary-released.** A bad rule update
  is the highest-severity incident type — it must roll out gradually and roll back instantly. Every
  filled application records the exact template+rule version used.
- **Golden test suite per form**: a corpus of (documents → expected fields → expected eligibility) that
  every template/rule change must pass in CI.
- **Provenance is permanent.** Even at scale, every produced PDF is reproducible from its provenance
  log + versions — essential for audits and disputes.

---

## 7. Cost model (order-of-magnitude, national scale)

Per active session (assuming on-device-first):
- OCR: ~0 (on-device) for the 80% happy path; cloud fallback ~₹0.5–2 for the rest.
- LLM: 3–6 calls, tiered → a few ₹ per session with caching.
- Voice: mostly on-device + cached prompts → sub-₹1.
- PDF + storage + infra: fractions of a ₹.

At ~2M sessions/day this is dominated by the cloud-fallback ratio. **Driving on-device coverage up and
cloud-fallback down is the single biggest cost lever** — hence it's an architectural default, not an
optimization. The plan is to fund the social mission by keeping marginal cost per assisted application
far below what touts charge (the fair-price meter makes this visible).

---

## 8. Reliability & operations

- **Multi-AZ** for RDS/Aurora and the API from Stage 1; **multi-region cells** at Stage 3.
- **Graceful degradation**: if the LLM is down, fall back to template-driven extraction + more voice
  gap-filling; if cloud OCR is down, rely on on-device + re-capture. The deterministic core (rules,
  DSL fill, PDF) works without any AI vendor.
- **Offline-first** (the roadmap item) becomes load-shedding at scale: capture+fill work on-device and
  sync later, flattening peaks for rural connectivity.
- **Observability**: per-stage latency, OCR confidence distributions, LLM tier mix, rules-gate
  decision counts, mismatch-catch rate, schemes-surfaced-not-asked — the same metrics that are the
  pitch KPIs (§ spec).
- **Idempotency keys** on every heavy op so queue retries never double-charge or double-produce.

---

## 9. Compliance & data residency at scale

- **DPDP Act 2023**: consent ledger, purpose limitation, data minimization, retention limits, and a
  user's right to erasure — all enforced by the ephemeral-by-default data model. At scale this means
  automated TTL deletion + audited erasure workflows.
- **Aadhaar Act**: full number never transmitted to or stored in the cloud; last-4 only; on-device
  masking is the enforcement point. No central honeypot of Aadhaar numbers — a deliberate
  architectural refusal.
- **Data residency**: all data in AWS Mumbai/Hyderabad regions; cells stay in-country.
- **Government integration** (Stage 2+): where official APIs exist (e.g. SECC/PM-JAY beneficiary
  lookup, DigiLocker for verified documents), integrate them to replace OCR guesses with verified
  facts — raising both accuracy and trust. Until then, be honest about database-gated eligibility.

---

## 10. The operational moat (not a server problem)

Two scaling assets are organizational, and they compound:

1. **The community-authorable form DSL** — state-format variance (land records, certificates) is the
   #1 cost. A library of versioned templates authored by operators/NGOs across states, with review,
   is how coverage scales without an engineer per form.
2. **The rejection-reason learning loop** — every bounced application feeds a validation/rule
   improvement ("this district won't accept an unstamped income certificate"). First-pass acceptance
   rate climbs with usage; the data becomes the moat.

Servers scale with money. These two scale with users — which is the right kind of scaling for a
public-good product.

---

## 11. Rollout sequence (concrete)

1. Harden the MVP, wire real keys, ship to one state in two languages.
2. Add SQS workers for OCR/LLM/PDF; move OCR on-device-default; add Redis + read replica.
3. Stand up the template-authoring tooling + golden-test CI; onboard NGO/CSC template authors.
4. Cell-split by region; Aurora; multi-AZ; canary pipeline for rule/template releases.
5. Integrate government APIs (DigiLocker, SECC) where available; expand languages and forms.
6. Continuous: drive on-device coverage up, watch the cost-per-session and acceptance-rate KPIs.
