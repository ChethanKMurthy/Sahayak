// Loads the shared 7-language UI strings. Source of truth is /shared/i18n/strings.json;
// this local copy is regenerated from it by scripts/sync-i18n.mjs (pre dev/build) so the
// web app builds standalone on Vercel without reaching outside its project root.
import strings from "./strings.shared.json";

export type Lang = "hi" | "en" | "kn" | "ta" | "te" | "mr" | "bn";

export const LANGS: { code: Lang; label: string; native: string }[] = [
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "en", label: "English", native: "English" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
];

type Bundle = Record<string, Record<string, string>>;
const bundle = strings as Bundle;

export function t(key: string, lang: Lang): string {
  const entry = bundle[key];
  if (!entry) return key;
  return entry[lang] || entry["en"] || key;
}

export function loc(map: Record<string, string> | undefined, lang: Lang): string {
  if (!map) return "";
  return map[lang] || map["en"] || Object.values(map)[0] || "";
}
