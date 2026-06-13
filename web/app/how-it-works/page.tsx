import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How it works — Sahayak",
  description: "Discover what you qualify for, fill a submittable application, and track it — in three steps.",
};

const STEPS = [
  {
    n: 1,
    title: "Discover",
    body: "Show your documents to the camera. Sahayak reads them on-device, then tells you every scheme and certificate you qualify for — including the ones you didn't know to ask for.",
  },
  {
    n: 2,
    title: "Execute",
    body: "Speak in your language. We pre-fill the form from your documents, ask only what's missing, read it back to you for consent, and produce a correctly-filled, submittable PDF with a checklist.",
  },
  {
    n: 3,
    title: "Track",
    body: "Get a reference number and gentle reminders so the application doesn't stall — and you never overpay a middleman for something that's free.",
  },
];

export default function HowItWorksPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <a href="/" className="text-sm font-medium text-orange-700 hover:underline">&larr; Back</a>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-gray-900">How Sahayak works</h1>
      <p className="mt-4 text-lg text-gray-600">
        Your phone becomes a government counter. No queues, no touts, no forms you can't read.
      </p>
      <ol className="mt-12 space-y-8">
        {STEPS.map((s) => (
          <li key={s.n} className="flex gap-5">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-orange-600 font-semibold text-white">
              {s.n}
            </span>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{s.title}</h2>
              <p className="mt-1 leading-relaxed text-gray-600">{s.body}</p>
            </div>
          </li>
        ))}
      </ol>
    </main>
  );
}
