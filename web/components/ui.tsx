"use client";
import { motion } from "framer-motion";
import {
  CreditCard, FileText, GraduationCap, IdCard, Landmark, ScrollText, Wheat, FileCheck2,
} from "lucide-react";
import type { Tier } from "@/lib/types";

export const TIER_META: Record<Tier, { color: string; bg: string; ring: string; label: string }> = {
  green: { color: "#1B873F", bg: "#E3F3E8", ring: "#1B873F", label: "Verified" },
  amber: { color: "#B26A00", bg: "#FBEFD6", ring: "#B26A00", label: "Please check" },
  red: { color: "#C62828", bg: "#FBE3E3", ring: "#C62828", label: "You told us this" },
};

export function TierDot({ tier, pulse }: { tier: Tier; pulse?: boolean }) {
  const m = TIER_META[tier];
  return (
    <span className="relative inline-flex h-3 w-3 shrink-0">
      {pulse && (
        <span className="absolute inline-flex h-full w-full rounded-full opacity-60 animate-pulsering"
          style={{ background: m.color }} />
      )}
      <span className="relative inline-flex h-3 w-3 rounded-full" style={{ background: m.color }} />
    </span>
  );
}

export function Pill({ children, tone = "ink" }: { children: React.ReactNode; tone?: string }) {
  const tones: Record<string, string> = {
    ink: "bg-paper-sunk text-ink-soft",
    saffron: "bg-saffron-soft text-saffron-deep",
    leaf: "bg-leaf-soft text-leaf",
    indigo: "bg-indigo-soft text-indigo",
  };
  return <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-xl2 bg-paper-card shadow-card ${className}`}>{children}</div>;
}

export function Button({
  children, onClick, variant = "primary", disabled, className = "", type = "button",
}: {
  children: React.ReactNode; onClick?: () => void; variant?: "primary" | "ghost" | "soft";
  disabled?: boolean; className?: string; type?: "button" | "submit";
}) {
  const v: Record<string, string> = {
    primary: "bg-saffron text-white hover:bg-saffron-deep shadow-card",
    soft: "bg-paper-sunk text-ink hover:bg-saffron-soft",
    ghost: "bg-transparent text-ink-soft hover:bg-paper-sunk",
  };
  return (
    <motion.button
      type={type} whileTap={{ scale: 0.97 }} onClick={onClick} disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-base font-semibold transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${v[variant]} ${className}`}>
      {children}
    </motion.button>
  );
}

const DOC_ICONS: Record<string, any> = {
  aadhaar: IdCard, ration_card: ScrollText, marksheet: GraduationCap, land_record: Wheat,
  income_cert: FileCheck2, caste_cert: FileCheck2, domicile_cert: FileCheck2,
  disability_cert: FileCheck2, death_cert: FileText, bank_passbook: CreditCard,
  passport_photo: IdCard, blank_form: FileText, unknown: FileText,
};
export function DocIcon({ type, className = "h-5 w-5" }: { type: string; className?: string }) {
  const I = DOC_ICONS[type] || FileText;
  return <I className={className} />;
}

export function CategoryIcon({ category, className = "h-5 w-5" }: { category: string; className?: string }) {
  const map: Record<string, any> = {
    pension: Landmark, scholarship: GraduationCap, identity: IdCard, certificate: FileCheck2,
    agriculture: Wheat, food_security: ScrollText, energy: FileText,
  };
  const I = map[category] || FileText;
  return <I className={className} />;
}
