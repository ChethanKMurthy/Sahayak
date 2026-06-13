"use client";
import { AnimatePresence, motion } from "framer-motion";
import { Mic, Sparkles } from "lucide-react";
import type { Dependency, EligibilityItem } from "@/lib/types";
import { CategoryIcon, DocIcon } from "./ui";

/** Animated phone-as-counter scan frame: a document with a sweeping scan line. */
export function ScanFrame({ scanning, docType = "aadhaar" }: { scanning: boolean; docType?: string }) {
  return (
    <div className="relative mx-auto aspect-[1.6/1] w-full max-w-sm overflow-hidden rounded-2xl border-2 border-dashed border-saffron/40 bg-paper-sunk">
      <div className="absolute inset-0 flex items-center justify-center text-ink-faint">
        <DocIcon type={docType} className="h-16 w-16 opacity-30" />
      </div>
      {/* corner brackets */}
      {["top-3 left-3 border-t-2 border-l-2", "top-3 right-3 border-t-2 border-r-2",
        "bottom-3 left-3 border-b-2 border-l-2", "bottom-3 right-3 border-b-2 border-r-2"].map((c) => (
        <span key={c} className={`absolute h-6 w-6 rounded-sm border-saffron ${c}`} />
      ))}
      {scanning && (
        <motion.div
          className="absolute left-0 right-0 h-0.5 bg-saffron shadow-[0_0_18px_4px_rgba(232,115,12,0.5)]"
          initial={{ top: "8%" }} animate={{ top: ["8%", "92%", "8%"] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }} />
      )}
    </div>
  );
}

/** Voice orb: pulsing mic with rings while listening/speaking. */
export function VoiceOrb({ active, speaking, onClick, label }: {
  active: boolean; speaking?: boolean; onClick?: () => void; label?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-3">
      <button onClick={onClick} aria-label={label || "Speak"}
        className="relative grid h-24 w-24 place-items-center rounded-full bg-saffron text-white shadow-lift transition-transform active:scale-95">
        {(active || speaking) && [0, 1, 2].map((i) => (
          <motion.span key={i} className="absolute inset-0 rounded-full border-2 border-saffron"
            initial={{ scale: 1, opacity: 0.5 }} animate={{ scale: 2.2, opacity: 0 }}
            transition={{ duration: 1.8, repeat: Infinity, delay: i * 0.5, ease: "easeOut" }} />
        ))}
        <Mic className="h-9 w-9" />
      </button>
      {label && <span className="text-sm font-medium text-ink-soft">{label}</span>}
    </div>
  );
}

/** Live waveform bars (decorative, animates while listening). */
export function Waveform({ active }: { active: boolean }) {
  return (
    <div className="flex h-10 items-center justify-center gap-1">
      {Array.from({ length: 18 }).map((_, i) => (
        <motion.span key={i} className="w-1 rounded-full bg-saffron/70"
          animate={active ? { height: [6, 8 + ((i * 7) % 26), 6] } : { height: 6 }}
          transition={{ duration: 0.6 + (i % 5) * 0.12, repeat: active ? Infinity : 0, ease: "easeInOut" }} />
      ))}
    </div>
  );
}

/** The entitlement-graph reveal — the "you also qualify for X" kicker moment. */
export function EntitlementGraph({ qualifies, surprises, dependencies, onPick, lang }: {
  qualifies: EligibilityItem[]; surprises: EligibilityItem[]; dependencies: Dependency[];
  onPick: (schemeId: string) => void; lang: string;
}) {
  return (
    <div className="space-y-6">
      {qualifies.length > 0 && (
        <div>
          <h3 className="mb-3 font-display text-lg text-ink">You qualify for</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {qualifies.map((s, i) => (
              <SchemeCard key={s.scheme_id} s={s} i={i} tone="leaf" onPick={onPick} />
            ))}
          </div>
        </div>
      )}

      <AnimatePresence>
        {surprises.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            <div className="mb-3 flex items-center gap-2">
              <motion.span animate={{ rotate: [0, 15, -10, 0] }} transition={{ duration: 1.2, repeat: Infinity, repeatDelay: 2 }}>
                <Sparkles className="h-5 w-5 text-saffron" />
              </motion.span>
              <h3 className="font-display text-lg text-ink">You also qualify — but didn't ask about</h3>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {surprises.map((s, i) => (
                <SchemeCard key={s.scheme_id} s={s} i={i} tone="saffron" highlight onPick={onPick} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {dependencies.length > 0 && (
        <div>
          <h3 className="mb-3 font-display text-lg text-ink">You need this first</h3>
          <div className="space-y-3">
            {dependencies.map((d) => (
              <motion.div key={d.scheme_id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="rounded-xl2 border border-amber/30 bg-amber-soft/60 p-4">
                <p className="font-semibold text-ink">{d.scheme_name}</p>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-ink-soft">
                  <span>requires</span>
                  {d.needs.map((n) => (
                    <button key={n.scheme_id} onClick={() => onPick(n.scheme_id)}
                      className="rounded-full bg-paper-card px-3 py-1 font-medium text-amber underline-offset-2 hover:underline">
                      {n.scheme_name} →
                    </button>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SchemeCard({ s, i, tone, highlight, onPick }: {
  s: EligibilityItem; i: number; tone: string; highlight?: boolean; onPick: (id: string) => void;
}) {
  return (
    <motion.button
      onClick={() => onPick(s.scheme_id)}
      initial={{ opacity: 0, y: 18, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: i * 0.08, type: "spring", stiffness: 220, damping: 22 }}
      whileHover={{ y: -3 }} whileTap={{ scale: 0.98 }}
      className={`group flex flex-col gap-2 rounded-xl2 p-4 text-left shadow-card transition-shadow hover:shadow-lift ${
        highlight ? "bg-gradient-to-br from-saffron-soft to-paper-card ring-1 ring-saffron/30" : "bg-paper-card"
      }`}>
      <div className="flex items-center gap-2">
        <span className={`grid h-9 w-9 place-items-center rounded-full ${tone === "leaf" ? "bg-leaf-soft text-leaf" : "bg-saffron-soft text-saffron-deep"}`}>
          <CategoryIcon category={s.category} />
        </span>
        <span className="font-semibold text-ink">{s.scheme_name}</span>
      </div>
      <p className="text-sm text-ink-soft">{s.benefit}</p>
      <p className="text-xs text-ink-faint">{s.why}</p>
      <span className="mt-1 text-sm font-semibold text-saffron group-hover:underline">Fill this form →</span>
    </motion.button>
  );
}
