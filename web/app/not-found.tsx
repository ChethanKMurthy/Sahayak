import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Page not found — Sahayak",
};

export default function NotFound() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center px-6 text-center">
      <p className="text-sm font-semibold uppercase tracking-widest text-orange-600">404</p>
      <h1 className="mt-3 text-3xl font-bold text-gray-900">We couldn&apos;t find that page</h1>
      <p className="mt-3 max-w-md text-gray-600">
        The link may be broken or the page may have moved. Let&apos;s get you back to the counter.
      </p>
      <Link
        href="/"
        className="mt-8 rounded-full bg-orange-600 px-6 py-3 font-medium text-white transition hover:bg-orange-700"
      >
        Go home
      </Link>
    </main>
  );
}
