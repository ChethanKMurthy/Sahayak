// Types mirroring the backend API responses.
export type Tier = "green" | "amber" | "red";

export interface ExtractedField { key: string; value: any; ocr_confidence: number; }
export interface DocOut {
  id: string; type: string; type_confidence: number;
  raw_text: string; fields: ExtractedField[]; ocr_quality: number; recapture_hint?: string | null;
}
export interface Mismatch {
  field: string; values: { value: any; document_id: string; doc_type: string }[];
  question: Record<string, string>; resolved_value?: any;
}
export interface CaptureResponse {
  documents: DocOut[]; mismatches: Mismatch[];
  recapture: { id: string; type: string; hint: string }[]; state: string;
}
export interface EligibilityItem {
  scheme_id: string; status: string; score: number; why: string;
  scheme_name: string; category: string; benefit: string; form_template_id?: string;
  missing_facts: string[]; missing_prerequisites: string[]; user_asked_for_it: boolean;
}
export interface Dependency {
  scheme_id: string; scheme_name: string;
  needs: { scheme_id: string; scheme_name: string }[]; needs_documents: string[];
}
export interface EligibilityView {
  qualifies: EligibilityItem[]; needs_prerequisite: EligibilityItem[];
  surprises: EligibilityItem[]; certificates: EligibilityItem[];
  dependencies: Dependency[]; all_results: EligibilityItem[];
}
export interface FilledField {
  key: string; label: string; value: any; tier: Tier; source: string;
  source_ref?: string; required: boolean; self_declared: boolean; verified: boolean; missing?: boolean;
}
export interface GapQuestion { key: string; label: string; question: string; type: string; options: string[]; }
export interface SelectFormResponse {
  form_id: string; title: string; filled: FilledField[];
  review: FilledField[]; missing: GapQuestion[]; state: string;
}
export interface TeachBack {
  script: string; intro: string; outro: string;
  lines: { text: string; tier: Tier; key: string }[]; audio_b64: string; state: string;
}
export interface ConsentResponse {
  pdf_url: string; checklist: ChecklistItem[]; output: OutputMeta; tracking_id: string; state: string;
}
export interface ChecklistItem {
  doc: string; label: string; copies: number; original: boolean; instruction: string; note: string;
}
export interface OutputMeta {
  submit_to: string; online_wall: boolean; online_wall_note: string;
  fair_price: { official_fee: number; tout_price: number; you_save: number; currency: string };
}
export interface Persona { id: string; label: Record<string, string>; asked_scheme: string; }
export interface Meta {
  languages: string[];
  personas: Persona[];
  schemes: { id: string; name: Record<string, string>; category: string;
    summary: Record<string, string>; benefit: Record<string, string> }[];
}
