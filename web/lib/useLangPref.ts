"use client";

import { useCallback, useEffect, useState } from "react";

export const SUPPORTED_LANGS = ["hi", "en", "kn", "ta", "te", "mr", "bn"] as const;
export type LangCode = (typeof SUPPORTED_LANGS)[number];

const KEY = "sahayak.lang";
const DEFAULT: LangCode = "hi";

function read(): LangCode {
  if (typeof window === "undefined") return DEFAULT;
  const stored = window.localStorage.getItem(KEY);
  return (SUPPORTED_LANGS as readonly string[]).includes(stored ?? "") ? (stored as LangCode) : DEFAULT;
}

/** SSR-safe persisted language preference: returns [lang, setLang]. */
export function useLangPref(): [LangCode, (next: LangCode) => void] {
  const [lang, setLangState] = useState<LangCode>(DEFAULT);

  // Hydrate from localStorage after mount to avoid SSR mismatch.
  useEffect(() => {
    setLangState(read());
  }, []);

  const setLang = useCallback((next: LangCode) => {
    setLangState(next);
    if (typeof window !== "undefined") window.localStorage.setItem(KEY, next);
  }, []);

  return [lang, setLang];
}
