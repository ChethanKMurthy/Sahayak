import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — Sahayak",
  description: "Why Sahayak exists: turning the right to a benefit into the benefit itself.",
};

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <a href="/" className="text-sm font-medium text-orange-700 hover:underline">&larr; Back</a>
      <h1 className="mt-4 text-4xl font-bold tracking-tight text-gray-900">About Sahayak</h1>
      <div className="mt-6 space-y-5 text-lg leading-relaxed text-gray-600">
        <p>
          India runs hundreds of welfare schemes, scholarships, pensions and certificates.
          The hard part is rarely the right — it's the paperwork: knowing what you qualify
          for, filling it without error, and getting it submitted without paying a middleman.
        </p>
        <p>
          Sahayak closes that gap. It reads your documents, applies a deterministic
          eligibility rules-gate (never a guess), and produces a correctly-filled,
          submittable application in your language — with the schemes you didn't know
          existed surfaced along the way.
        </p>
        <p className="font-medium text-gray-900">
          Our measure of success is simple: a benefit claimed that would otherwise have
          been left on the table.
        </p>
      </div>
    </main>
  );
}
