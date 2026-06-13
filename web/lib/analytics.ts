/**
 * Privacy-respecting, consent-gated analytics.
 *
 * No-ops unless the user has opted in (see `setAnalyticsConsent`). When enabled,
 * events are POSTed to NEXT_PUBLIC_ANALYTICS_URL using `navigator.sendBeacon`
 * so they don't block navigation. No PII is ever sent — only event names + props
 * the caller chooses.
 */

export type AnalyticsEvent =
  | "session_started"
  | "documents_captured"
  | "eligibility_viewed"
  | "form_filled"
  | "consent_given"
  | "pdf_downloaded"
  | "language_changed";

const CONSENT_KEY = "sahayak.analytics.consent";

export function setAnalyticsConsent(granted: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(CONSENT_KEY, granted ? "1" : "0");
}

export function hasAnalyticsConsent(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(CONSENT_KEY) === "1";
}

export function track(event: AnalyticsEvent, props: Record<string, string | number | boolean> = {}): void {
  if (typeof window === "undefined" || !hasAnalyticsConsent()) return;
  const url = process.env.NEXT_PUBLIC_ANALYTICS_URL;
  if (!url) return;
  const payload = JSON.stringify({ event, props, ts: Date.now() });
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([payload], { type: "application/json" }));
    } else {
      void fetch(url, { method: "POST", body: payload, keepalive: true });
    }
  } catch {
    /* analytics must never break the app */
  }
}
