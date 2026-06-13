# Sahayak — Web app (Next.js 14)

Voice-first, animated web client mirroring the Flutter app and backend flow. Warm,
government-grade design with Framer Motion animations: scan frame, voice orb, live
waveform, confidence-tier transitions, and the entitlement-graph "you also qualify" reveal.

## Run

```bash
npm install
cp .env.local.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                          # http://localhost:3000  (proxies /api → backend)
```

The backend must be running (see `../backend/README.md`). `/api/*` is proxied to it via
`next.config.mjs`, so the browser hits a single origin.

## Flow

`welcome → capture → consistency → eligibility → fill → teach-back → output`, driven from
`app/page.tsx`. Voice uses the browser Web Speech API (`lib/useVoice.ts`); when the backend
has Bhashini/AWS keys, audio can be routed server-side instead.

## Notable pieces

- `components/Visuals.tsx` — ScanFrame, VoiceOrb, Waveform, EntitlementGraph
- `components/ui.tsx` — tier dots, scheme/category icons, buttons (warm palette)
- `lib/api.ts` — typed client; `lib/i18n.ts` — loads the shared 7-language strings
- `lib/types.ts` — mirrors the backend responses

## Build / deploy

```bash
npm run build       # standalone output for Docker (see ../web/Dockerfile)
```
CI builds on every push; `deploy.yml` ships the container to AWS App Runner.
