import type {
  CaptureResponse, ConsentResponse, EligibilityView, Meta, SelectFormResponse, TeachBack,
} from "./types";

// Same-origin /api proxied to FastAPI (see next.config.mjs).
async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status}: ${txt}`);
  }
  return res.json();
}

export const api = {
  meta: () => j<Meta>("/api/meta"),
  createSession: (language: string, operator_mode = false) =>
    j<{ id: string; state: string; language: string }>("/api/session", {
      method: "POST", body: JSON.stringify({ language, operator_mode }),
    }),
  capture: (sid: string, body: { persona?: string; documents?: any[]; asked_scheme?: string }) =>
    j<CaptureResponse>(`/api/session/${sid}/capture`, { method: "POST", body: JSON.stringify(body) }),
  resolve: (sid: string, resolutions: Record<string, any>) =>
    j<{ state: string }>(`/api/session/${sid}/resolve`, {
      method: "POST", body: JSON.stringify({ resolutions }),
    }),
  answer: (sid: string, answers: Record<string, any>) =>
    j<{ state: string }>(`/api/session/${sid}/answer`, {
      method: "POST", body: JSON.stringify({ answers }),
    }),
  eligibility: (sid: string) => j<EligibilityView>(`/api/session/${sid}/eligibility`),
  selectForm: (sid: string, scheme_id: string) =>
    j<SelectFormResponse>(`/api/session/${sid}/select-form`, {
      method: "POST", body: JSON.stringify({ scheme_id }),
    }),
  teachback: (sid: string) => j<TeachBack>(`/api/session/${sid}/teachback`),
  consent: (sid: string, confirmed: boolean, edits: Record<string, any> = {}, method = "voice") =>
    j<ConsentResponse>(`/api/session/${sid}/consent`, {
      method: "POST", body: JSON.stringify({ confirmed, method, edits }),
    }),
  setReference: (tid: string, reference_number: string, submitted_to = "") =>
    j<any>(`/api/tracking/${tid}/reference`, {
      method: "POST", body: JSON.stringify({ reference_number, submitted_to }),
    }),
  tts: (text: string, language: string) =>
    j<{ audio_b64: string }>("/api/voice/tts", {
      method: "POST", body: JSON.stringify({ text, language }),
    }),
};
