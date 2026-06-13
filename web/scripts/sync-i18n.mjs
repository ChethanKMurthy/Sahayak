// Regenerates web/lib/strings.shared.json from the monorepo single-source-of-truth
// (/shared/i18n/strings.json). Runs before dev/build. On Vercel the source isn't
// uploaded (web is deployed as its own root), so we keep the last vendored copy.
import { existsSync, copyFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = resolve(here, "../../shared/i18n/strings.json"); // repo /shared
const dest = resolve(here, "../lib/strings.shared.json");

if (existsSync(src)) {
  copyFileSync(src, dest);
  console.log("[sync-i18n] vendored strings.shared.json from /shared");
} else {
  console.log("[sync-i18n] /shared not present (e.g. Vercel) — using existing vendored copy");
}
