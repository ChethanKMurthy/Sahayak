"use client";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowRight, Check, FileDown, Info, Landmark, MapPin, Mic, ReceiptText, ShieldCheck, Volume2,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { EntitlementGraph, ScanFrame, VoiceOrb, Waveform } from "@/components/Visuals";
import { Button, Card, DocIcon, Pill, TierDot, TIER_META } from "@/components/ui";
import { api } from "@/lib/api";
import { LANGS, Lang, loc, t } from "@/lib/i18n";
import type {
  CaptureResponse, ConsentResponse, EligibilityView, Meta, SelectFormResponse, TeachBack,
} from "@/lib/types";
import { useVoice } from "@/lib/useVoice";

type Stage = "welcome" | "capture" | "consistency" | "eligibility" | "fill" | "teachback" | "output";
const STEPS: { key: Stage; label: string }[] = [
  { key: "capture", label: "Capture" }, { key: "consistency", label: "Verify" },
  { key: "eligibility", label: "Discover" }, { key: "fill", label: "Fill" },
  { key: "teachback", label: "Confirm" }, { key: "output", label: "Submit" },
];

export default function Page() {
  const [lang, setLang] = useState<Lang>("hi");
  const [operator, setOperator] = useState(false);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [sid, setSid] = useState<string | null>(null);
  const [stage, setStage] = useState<Stage>("welcome");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [capture, setCapture] = useState<CaptureResponse | null>(null);
  const [elig, setElig] = useState<EligibilityView | null>(null);
  const [form, setForm] = useState<SelectFormResponse | null>(null);
  const [teach, setTeach] = useState<TeachBack | null>(null);
  const [output, setOutput] = useState<ConsentResponse | null>(null);

  useEffect(() => { api.meta().then(setMeta).catch((e) => setErr(String(e))); }, []);

  const run = useCallback(async (fn: () => Promise<void>) => {
    setBusy(true); setErr(null);
    try { await fn(); } catch (e: any) { setErr(e?.message || String(e)); } finally { setBusy(false); }
  }, []);

  return (
    <div className="bg-grid min-h-dvh">
      <Header lang={lang} setLang={setLang} operator={operator} setOperator={setOperator}
        showSteps={stage !== "welcome"} stage={stage} />
      <main className="mx-auto max-w-3xl px-4 pb-24 pt-6">
        {err && (
          <div className="mb-4 rounded-xl border border-flag/30 bg-flag-soft px-4 py-2 text-sm text-flag">{err}</div>
        )}
        <AnimatePresence mode="wait">
          <motion.div key={stage}
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.35, ease: "easeOut" }}>
            {stage === "welcome" && meta && (
              <Welcome meta={meta} lang={lang} setLang={setLang} operator={operator} setOperator={setOperator}
                busy={busy}
                onStart={(persona) => run(async () => {
                  const s = await api.createSession(lang, operator);
                  setSid(s.id);
                  setStage("capture");
                  // kick off capture immediately for the chosen persona
                  const cap = await api.capture(s.id, { persona });
                  setCapture(cap);
                  if (cap.mismatches.length) setStage("consistency");
                  else { const e = await api.eligibility(s.id); setElig(e); setStage("eligibility"); }
                })} />
            )}

            {stage === "capture" && (
              <CaptureView capture={capture} lang={lang} busy={busy} />
            )}

            {stage === "consistency" && capture && sid && (
              <ConsistencyView capture={capture} lang={lang} busy={busy}
                onResolve={(res) => run(async () => {
                  await api.resolve(sid, res);
                  const e = await api.eligibility(sid); setElig(e); setStage("eligibility");
                })} />
            )}

            {stage === "eligibility" && elig && sid && (
              <div className="space-y-5">
                <SectionTitle icon={<Landmark className="h-5 w-5" />}
                  title="What you're entitled to" sub="Based on your documents and the rules — checked in code, not guessed." />
                <EntitlementGraph qualifies={elig.qualifies} surprises={elig.surprises}
                  dependencies={elig.dependencies} lang={lang}
                  onPick={(scheme_id) => run(async () => {
                    const f = await api.selectForm(sid, scheme_id);
                    setForm({ ...f, scheme_id } as any); setStage("fill");
                  })} />
                {elig.certificates.length > 0 && (
                  <p className="text-sm text-ink-faint">
                    You can also obtain: {elig.certificates.map((c) => c.scheme_name).join(", ")}.
                  </p>
                )}
              </div>
            )}

            {stage === "fill" && form && sid && (
              <FillView form={form} lang={lang} sid={sid} busy={busy}
                onAnswered={(updated) => setForm(updated)}
                onReady={() => run(async () => {
                  const tb = await api.teachback(sid); setTeach(tb); setStage("teachback");
                })} />
            )}

            {stage === "teachback" && teach && sid && (
              <TeachBackView teach={teach} lang={lang} busy={busy}
                onConfirm={(method) => run(async () => {
                  const out = await api.consent(sid, true, {}, method); setOutput(out); setStage("output");
                })} />
            )}

            {stage === "output" && output && sid && (
              <OutputView output={output} lang={lang} sid={sid} />
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

/* ─────────────────────────────── Header ─────────────────────────────────── */
function Header({ lang, setLang, operator, setOperator, showSteps, stage }: {
  lang: Lang; setLang: (l: Lang) => void; operator: boolean; setOperator: (b: boolean) => void;
  showSteps: boolean; stage: Stage;
}) {
  const idx = STEPS.findIndex((s) => s.key === stage);
  return (
    <header className="glass sticky top-0 z-20 border-b border-ink/5">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-saffron text-white font-display text-lg">स</span>
          <div className="leading-tight">
            <p className="font-display text-lg font-semibold">{t("app_name", lang)}</p>
            <p className="text-[11px] text-ink-faint">{t("tagline", lang)}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setOperator(!operator)}
            className={`hidden rounded-full px-3 py-1.5 text-xs font-medium sm:inline-flex ${operator ? "bg-indigo text-white" : "bg-paper-sunk text-ink-soft"}`}>
            {t("operator_mode", lang)}
          </button>
          <select value={lang} onChange={(e) => setLang(e.target.value as Lang)}
            className="rounded-full bg-paper-sunk px-3 py-1.5 text-sm font-medium text-ink">
            {LANGS.map((l) => <option key={l.code} value={l.code}>{l.native}</option>)}
          </select>
        </div>
      </div>
      {showSteps && (
        <div className="mx-auto flex max-w-3xl items-center gap-1 px-4 pb-3">
          {STEPS.map((s, i) => (
            <div key={s.key} className="flex flex-1 items-center gap-1">
              <div className={`h-1.5 flex-1 rounded-full transition-colors ${i <= idx ? "bg-saffron" : "bg-paper-sunk"}`} />
            </div>
          ))}
        </div>
      )}
    </header>
  );
}

function SectionTitle({ icon, title, sub }: { icon: React.ReactNode; title: string; sub?: string }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 grid h-9 w-9 place-items-center rounded-full bg-saffron-soft text-saffron-deep">{icon}</span>
      <div>
        <h2 className="font-display text-2xl font-semibold leading-tight">{title}</h2>
        {sub && <p className="text-sm text-ink-soft">{sub}</p>}
      </div>
    </div>
  );
}

/* ─────────────────────────────── Welcome ────────────────────────────────── */
function Welcome({ meta, lang, setLang, operator, setOperator, onStart, busy }: {
  meta: Meta; lang: Lang; setLang: (l: Lang) => void; operator: boolean; setOperator: (b: boolean) => void;
  onStart: (persona: string) => void; busy: boolean;
}) {
  return (
    <div className="space-y-8 py-6">
      <div className="text-center">
        <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}
          className="font-display text-4xl font-semibold leading-tight sm:text-5xl">
          {t("tagline", lang)}
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
          className="mx-auto mt-3 max-w-xl text-ink-soft">
          Place your documents, speak one answer in your language, and out comes a correctly-filled,
          submittable application — plus the schemes you didn't know you qualified for.
        </motion.p>
      </div>

      <Card className="p-5">
        <p className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink-soft">
          <ShieldCheck className="h-4 w-4 text-leaf" /> {t("aadhaar_safe", lang)}
        </p>
        <p className="mb-4 font-medium">Pick a demo profile to see the full flow (synthetic data — no real PII):</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {meta.personas.map((p, i) => (
            <motion.button key={p.id} disabled={busy} onClick={() => onStart(p.id)}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }}
              className="rounded-xl2 border border-ink/5 bg-paper p-4 text-left shadow-card hover:shadow-lift disabled:opacity-50">
              <p className="font-semibold">{loc(p.label, lang)}</p>
              <p className="mt-1 text-sm text-saffron">Came asking about: {p.asked_scheme.replace(/-/g, " ")}</p>
            </motion.button>
          ))}
        </div>
      </Card>

      <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-ink-faint">
        <span>Language:</span>
        {LANGS.map((l) => (
          <button key={l.code} onClick={() => setLang(l.code)}
            className={`rounded-full px-3 py-1 ${lang === l.code ? "bg-saffron text-white" : "bg-paper-sunk"}`}>
            {l.native}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ─────────────────────────────── Capture ────────────────────────────────── */
function CaptureView({ capture, lang, busy }: { capture: CaptureResponse | null; lang: Lang; busy: boolean }) {
  const scanning = !capture || busy;
  return (
    <div className="space-y-6">
      <SectionTitle icon={<DocIcon type="aadhaar" className="h-5 w-5" />}
        title={t("capture", lang)} sub={t("place_document", lang)} />
      <ScanFrame scanning={scanning} docType={capture?.documents?.[0]?.type || "aadhaar"} />
      {!capture ? (
        <p className="text-center text-ink-soft">{t("extracting", lang)}</p>
      ) : (
        <div className="space-y-3">
          {capture.documents.map((d, i) => (
            <motion.div key={d.id} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}>
              <Card className="p-4">
                <div className="mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-2 font-semibold capitalize">
                    <DocIcon type={d.type} /> {d.type.replace(/_/g, " ")}
                  </span>
                  <Pill tone={d.ocr_quality > 0.85 ? "leaf" : "saffron"}>
                    OCR {Math.round(d.ocr_quality * 100)}%
                  </Pill>
                </div>
                <div className="flex flex-wrap gap-2">
                  {d.fields.map((f) => (
                    <span key={f.key} className="rounded-lg bg-paper-sunk px-2.5 py-1 text-sm">
                      <span className="text-ink-faint">{f.key.replace(/_/g, " ")}: </span>
                      <span className="font-medium">{String(f.value)}</span>
                    </span>
                  ))}
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────── Consistency ───────────────────────────────── */
function ConsistencyView({ capture, lang, onResolve, busy }: {
  capture: CaptureResponse; lang: Lang; onResolve: (r: Record<string, any>) => void; busy: boolean;
}) {
  const [choices, setChoices] = useState<Record<string, any>>({});
  const m = capture.mismatches;
  const allChosen = m.every((mm) => choices[mm.field] !== undefined);
  return (
    <div className="space-y-6">
      <SectionTitle icon={<Info className="h-5 w-5" />} title={t("review_mismatch", lang)}
        sub="We found the same detail spelled differently across your documents — the #1 cause of rejection." />
      {m.map((mm) => (
        <Card key={mm.field} className="p-5">
          <p className="mb-3 font-medium">{loc(mm.question, lang)}</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {mm.values.map((v) => {
              const picked = choices[mm.field] === v.value;
              return (
                <button key={v.document_id} onClick={() => setChoices({ ...choices, [mm.field]: v.value })}
                  className={`rounded-xl2 border p-3 text-left transition-all ${picked ? "border-saffron bg-saffron-soft shadow-glow" : "border-ink/10 bg-paper hover:border-saffron/40"}`}>
                  <span className="block text-lg font-semibold">{String(v.value)}</span>
                  <span className="text-xs capitalize text-ink-faint">from {v.doc_type.replace(/_/g, " ")}</span>
                  {picked && <Check className="mt-1 inline h-4 w-4 text-saffron" />}
                </button>
              );
            })}
          </div>
        </Card>
      ))}
      <Button disabled={!allChosen || busy} onClick={() => onResolve(choices)} className="w-full">
        Confirm and continue <ArrowRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

/* ─────────────────────────────── Fill ───────────────────────────────────── */
function FillView({ form, lang, sid, onAnswered, onReady, busy }: {
  form: SelectFormResponse; lang: Lang; sid: string;
  onAnswered: (f: SelectFormResponse) => void; onReady: () => void; busy: boolean;
}) {
  const voice = useVoice(lang);
  const [openSource, setOpenSource] = useState<string | null>(null);
  const [answering, setAnswering] = useState<string | null>(null);

  const askByVoice = async (key: string, label: string) => {
    setAnswering(key);
    if (voice.supported) { await voice.speak(label); }
    const said = voice.supported ? await voice.listen() : window.prompt(label) || "";
    setAnswering(null);
    if (!said) return;
    await api.answer(sid, { [key]: coerce(said) });
    const updated = await api.selectForm(sid, schemeOf(form));
    onAnswered({ ...updated, scheme_id: schemeOf(form) } as any);
  };

  const typeAnswer = async (key: string, value: any) => {
    await api.answer(sid, { [key]: coerce(value) });
    const updated = await api.selectForm(sid, schemeOf(form));
    onAnswered({ ...updated, scheme_id: schemeOf(form) } as any);
  };

  return (
    <div className="space-y-6">
      <SectionTitle icon={<ReceiptText className="h-5 w-5" />} title={form.title}
        sub="Tap any field to see where its value came from. Only ? and ! fields need your check." />

      <Card className="divide-y divide-ink/5">
        {form.filled.map((f) => {
          const m = TIER_META[f.tier];
          const open = openSource === f.key;
          return (
            <div key={f.key} className="p-4">
              <div className="flex items-center justify-between gap-3">
                <button onClick={() => setOpenSource(open ? null : f.key)} className="flex flex-1 items-center gap-3 text-left">
                  <TierDot tier={f.tier} pulse={f.tier !== "green" && !f.missing} />
                  <span>
                    <span className="block text-sm text-ink-faint">{f.label}</span>
                    <span className={`block text-lg font-medium ${f.missing ? "text-ink-faint italic" : ""}`}>
                      {f.missing || f.value == null || f.value === "" ? "—" : String(f.value)}
                    </span>
                  </span>
                </button>
                {f.missing && f.required && (
                  <Button variant="soft" onClick={() => askByVoice(f.key, f.label)}>
                    <Mic className="h-4 w-4" /> Speak
                  </Button>
                )}
                {!f.missing && <Pill tone={f.tier === "green" ? "leaf" : "saffron"}>{m.label}</Pill>}
              </div>
              <AnimatePresence>
                {open && (
                  <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-2 overflow-hidden rounded-lg bg-paper-sunk px-3 py-2 text-sm text-ink-soft">
                    <Info className="mr-1 inline h-3.5 w-3.5" /> {t("source_label", lang)}: {f.source || "—"}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </Card>

      {answering && (
        <Card className="p-5">
          <p className="mb-2 text-center text-sm text-ink-soft">{t("speak_now", lang)}</p>
          <Waveform active={voice.listening} />
        </Card>
      )}

      {form.missing.length > 0 ? (
        <Card className="space-y-4 p-5">
          <p className="font-medium">A few details we couldn't read — answer by voice or type:</p>
          {form.missing.map((q) => (
            <div key={q.key} className="space-y-2">
              <p className="flex items-center gap-2 font-medium"><Volume2 className="h-4 w-4 text-saffron" /> {q.question}</p>
              {q.options.length ? (
                <div className="flex flex-wrap gap-2">
                  {q.options.map((o) => (
                    <button key={o} onClick={() => typeAnswer(q.key, o)}
                      className="rounded-full bg-paper-sunk px-4 py-2 text-sm font-medium hover:bg-saffron-soft">{o}</button>
                  ))}
                </div>
              ) : (
                <div className="flex gap-2">
                  <Button variant="soft" onClick={() => askByVoice(q.key, q.label)}><Mic className="h-4 w-4" /> Speak</Button>
                  <TypeField onSubmit={(v) => typeAnswer(q.key, v)} />
                </div>
              )}
            </div>
          ))}
        </Card>
      ) : (
        <Button disabled={busy} onClick={onReady} className="w-full">
          Looks good — read it back to me <ArrowRight className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}

function TypeField({ onSubmit }: { onSubmit: (v: string) => void }) {
  const [v, setV] = useState("");
  return (
    <form className="flex flex-1 gap-2" onSubmit={(e) => { e.preventDefault(); if (v) onSubmit(v); setV(""); }}>
      <input value={v} onChange={(e) => setV(e.target.value)} placeholder="type answer"
        className="flex-1 rounded-full border border-ink/10 bg-paper px-4 py-2 text-base" />
      <Button type="submit" variant="soft">Add</Button>
    </form>
  );
}

/* ─────────────────────────────── Teach-back ─────────────────────────────── */
function TeachBackView({ teach, lang, onConfirm, busy }: {
  teach: TeachBack; lang: Lang; onConfirm: (method: string) => void; busy: boolean;
}) {
  const voice = useVoice(lang);
  const [active, setActive] = useState(-1);

  const play = useCallback(async () => {
    for (let i = 0; i < teach.lines.length; i++) {
      setActive(i);
      // eslint-disable-next-line no-await-in-loop
      await voice.speak(teach.lines[i].text);
    }
    setActive(-1);
  }, [teach, voice]);

  useEffect(() => { const tmo = setTimeout(play, 400); return () => { clearTimeout(tmo); voice.shutUp(); }; }, []); // eslint-disable-line

  const confirmByVoice = async () => {
    const said = voice.supported ? await voice.listen() : "yes";
    if (/yes|haan|हाँ|ہاں|ಹೌದು|ஆம்|అవును|হ্যাঁ|होय/i.test(said)) onConfirm("voice");
  };

  return (
    <div className="space-y-6">
      <SectionTitle icon={<Volume2 className="h-5 w-5" />} title={t("read_back", lang)}
        sub="We read your filled form aloud. Nothing is produced until you confirm — we never auto-submit." />
      <Card className="space-y-1 p-5">
        {teach.lines.map((l, i) => (
          <motion.div key={l.key} animate={{ scale: active === i ? 1.02 : 1, opacity: active === i ? 1 : 0.7 }}
            className={`flex items-center gap-2 rounded-lg px-3 py-2 ${active === i ? "bg-saffron-soft" : ""}`}>
            <TierDot tier={l.tier} pulse={active === i} />
            <span className={active === i ? "font-semibold" : ""}>{l.text}</span>
          </motion.div>
        ))}
      </Card>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Button variant="soft" onClick={play}><Volume2 className="h-4 w-4" /> Play again</Button>
        <Button onClick={confirmByVoice} className="flex-1"><Mic className="h-4 w-4" /> Say "yes" to confirm</Button>
        <Button variant="soft" disabled={busy} onClick={() => onConfirm("tap")}><Check className="h-4 w-4" /> {t("confirm_consent", lang)}</Button>
      </div>
    </div>
  );
}

/* ─────────────────────────────── Output ─────────────────────────────────── */
function OutputView({ output, lang, sid }: { output: ConsentResponse; lang: Lang; sid: string }) {
  const [ref, setRef] = useState("");
  const [tracked, setTracked] = useState(false);
  const fp = output.output.fair_price;
  return (
    <div className="space-y-6">
      <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        className="grid place-items-center gap-2 py-2 text-center">
        <span className="grid h-16 w-16 place-items-center rounded-full bg-leaf-soft text-leaf">
          <Check className="h-9 w-9" />
        </span>
        <h2 className="font-display text-2xl font-semibold">Your application is ready</h2>
        <p className="text-ink-soft">A draft for your confirmation — not auto-submitted.</p>
      </motion.div>

      <a href={output.pdf_url} target="_blank" rel="noreferrer">
        <Button className="w-full"><FileDown className="h-5 w-5" /> {t("download_pdf", lang)}</Button>
      </a>

      <Card className="p-5">
        <h3 className="mb-3 font-display text-lg">{t("checklist", lang)}</h3>
        <ul className="space-y-2">
          {output.checklist.map((c) => (
            <li key={c.doc} className="flex items-start gap-2">
              <span className="mt-1 grid h-5 w-5 place-items-center rounded border border-ink/20 text-xs">☐</span>
              <span><span className="font-medium">{c.instruction}</span> {c.label}
                {c.note && <span className="text-ink-faint"> — {c.note}</span>}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="p-5">
        <h3 className="mb-1 flex items-center gap-2 font-display text-lg"><MapPin className="h-5 w-5 text-saffron" /> {t("where_submit", lang)}</h3>
        <p className="text-ink-soft">{output.output.submit_to}</p>
        {output.output.online_wall && (
          <p className="mt-2 rounded-lg bg-amber-soft px-3 py-2 text-sm text-amber">⚠ {output.output.online_wall_note}</p>
        )}
      </Card>

      <Card className="p-5">
        <h3 className="mb-3 font-display text-lg">{t("fair_price", lang)}</h3>
        <div className="flex items-end gap-4">
          <Bar label="Official fee" value={fp.official_fee} max={fp.tout_price} tone="leaf" />
          <Bar label="Typical tout" value={fp.tout_price} max={fp.tout_price} tone="flag" />
        </div>
        <p className="mt-3 text-center font-semibold text-leaf">You save ₹{fp.you_save}</p>
      </Card>

      <Card className="p-5">
        <h3 className="mb-2 font-display text-lg">{t("track", lang)}</h3>
        {tracked ? (
          <p className="text-leaf">Saved. We'll remind you to follow up in 30 days.</p>
        ) : (
          <form className="flex gap-2" onSubmit={async (e) => {
            e.preventDefault(); if (!ref) return; await api.setReference(output.tracking_id, ref); setTracked(true);
          }}>
            <input value={ref} onChange={(e) => setRef(e.target.value)}
              placeholder="Acknowledgement / reference number"
              className="flex-1 rounded-full border border-ink/10 bg-paper px-4 py-2.5" />
            <Button type="submit" variant="soft">Save</Button>
          </form>
        )}
      </Card>
    </div>
  );
}

function Bar({ label, value, max, tone }: { label: string; value: number; max: number; tone: string }) {
  const pct = max > 0 ? Math.max((value / max) * 100, 4) : 4;
  const c = tone === "leaf" ? "#1B873F" : "#C62828";
  return (
    <div className="flex-1">
      <div className="flex h-28 items-end">
        <motion.div initial={{ height: 0 }} animate={{ height: `${pct}%` }} transition={{ duration: 0.7 }}
          className="w-full rounded-t-lg" style={{ background: c }} />
      </div>
      <p className="mt-1 text-center text-sm font-medium">₹{value}</p>
      <p className="text-center text-xs text-ink-faint">{label}</p>
    </div>
  );
}

/* helpers */
function coerce(v: any): any {
  if (v === "true" || v === true) return true;
  if (v === "false" || v === false) return false;
  if (typeof v === "string" && /^\d+(\.\d+)?$/.test(v.trim())) return Number(v);
  return v;
}
// The select-form endpoint takes a scheme id; we stored the scheme via the form.
// Forms whose id equals the scheme id work directly; otherwise we keep the scheme
// id on the form object below.
function schemeOf(form: SelectFormResponse & { scheme_id?: string }): string {
  return (form as any).scheme_id || form.form_id;
}
