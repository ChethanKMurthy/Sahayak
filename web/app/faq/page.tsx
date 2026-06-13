import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "FAQ — Sahayak",
  description: "Common questions about privacy, eligibility, languages and cost.",
};

const FAQS = [
  {
    q: "Is my Aadhaar / personal data safe?",
    a: "Documents are read on-device where possible, and we store metadata — never your full Aadhaar number. The audit trail is append-only and built for DPDP compliance.",
  },
  {
    q: "Does an AI decide whether I qualify?",
    a: "No. Eligibility is decided by a deterministic rules-gate over the facts in your documents. The AI only explains the result and helps phrase questions — it never decides.",
  },
  {
    q: "Which languages are supported?",
    a: "Hindi, English, Kannada, Tamil, Telugu, Marathi and Bengali — across the whole flow, including voice.",
  },
  {
    q: "Does it cost anything?",
    a: "The government fees are what they are — usually small or zero. Sahayak shows you the official fee so you never overpay a tout for a free service.",
  },
];

export default function FaqPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <a href="/" className="text-sm font-medium text-orange-700 hover:underline">&larr; Back</a>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-gray-900">Frequently asked questions</h1>
      <div className="mt-10 divide-y divide-gray-200">
        {FAQS.map((f) => (
          <details key={f.q} className="group py-5">
            <summary className="cursor-pointer list-none text-lg font-semibold text-gray-900 marker:content-none">
              <span className="inline-flex w-full items-center justify-between gap-4">
                {f.q}
                <span className="text-orange-600 transition-transform group-open:rotate-45">+</span>
              </span>
            </summary>
            <p className="mt-3 leading-relaxed text-gray-600">{f.a}</p>
          </details>
        ))}
      </div>
    </main>
  );
}
