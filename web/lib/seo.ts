import type { Metadata } from "next";

const SITE = "Sahayak";
const DEFAULT_DESCRIPTION =
  "Capture your documents, speak in your language, and out comes a correctly-filled, submittable government application.";

const LOCALES = ["hi", "en", "kn", "ta", "te", "mr", "bn"] as const;

/** Build consistent Next.js Metadata for a page, including Open Graph + locale alternates. */
export function buildMetadata(opts: {
  title?: string;
  description?: string;
  path?: string;
} = {}): Metadata {
  const title = opts.title ? `${opts.title} — ${SITE}` : `${SITE} — your government counter, on your phone`;
  const description = opts.description ?? DEFAULT_DESCRIPTION;
  const path = opts.path ?? "/";

  return {
    title,
    description,
    alternates: {
      canonical: path,
      languages: Object.fromEntries(LOCALES.map((l) => [l, `${path}?lang=${l}`])),
    },
    openGraph: {
      title,
      description,
      siteName: SITE,
      type: "website",
      locale: "en_IN",
    },
    twitter: { card: "summary_large_image", title, description },
  };
}
