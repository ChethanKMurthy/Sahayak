"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import type { Lang } from "./i18n";

const BCP47: Record<Lang, string> = {
  hi: "hi-IN", en: "en-IN", kn: "kn-IN", ta: "ta-IN", te: "te-IN", mr: "mr-IN", bn: "bn-IN",
};

// Web Speech API is the on-device voice path in the browser (mock-mode default).
// When the backend has Bhashini/AWS keys, audio could be routed there instead.
export function useVoice(lang: Lang) {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [supported, setSupported] = useState(true);
  const recogRef = useRef<any>(null);

  useEffect(() => {
    const SR = (typeof window !== "undefined" &&
      ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)) || null;
    setSupported(!!SR && typeof window !== "undefined" && !!window.speechSynthesis);
  }, []);

  const listen = useCallback(
    () =>
      new Promise<string>((resolve) => {
        const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (!SR) return resolve("");
        const r = new SR();
        recogRef.current = r;
        r.lang = BCP47[lang];
        r.interimResults = false;
        r.maxAlternatives = 1;
        r.onresult = (e: any) => resolve(e.results[0][0].transcript);
        r.onerror = () => resolve("");
        r.onend = () => setListening(false);
        setListening(true);
        r.start();
      }),
    [lang]
  );

  const stop = useCallback(() => {
    recogRef.current?.stop?.();
    setListening(false);
  }, []);

  const speak = useCallback(
    (text: string) =>
      new Promise<void>((resolve) => {
        if (typeof window === "undefined" || !window.speechSynthesis) return resolve();
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = BCP47[lang];
        u.rate = 0.95;
        const match = window.speechSynthesis.getVoices().find((v) => v.lang === BCP47[lang]);
        if (match) u.voice = match;
        u.onend = () => { setSpeaking(false); resolve(); };
        u.onerror = () => { setSpeaking(false); resolve(); };
        setSpeaking(true);
        window.speechSynthesis.speak(u);
      }),
    [lang]
  );

  const shutUp = useCallback(() => {
    if (typeof window !== "undefined") window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);

  return { listen, stop, speak, shutUp, listening, speaking, supported };
}
