import type { ReactNode } from "react";

type Variant = "info" | "success" | "warning" | "error";

const STYLES: Record<Variant, string> = {
  info: "bg-blue-50 text-blue-900 border-blue-200",
  success: "bg-green-50 text-green-900 border-green-200",
  warning: "bg-amber-50 text-amber-900 border-amber-200",
  error: "bg-red-50 text-red-900 border-red-200",
};

const ICON: Record<Variant, string> = { info: "ℹ", success: "✓", warning: "⚠", error: "✕" };

/** An inline, accessible alert banner. */
export function Alert({
  variant = "info",
  title,
  children,
}: {
  variant?: Variant;
  title?: string;
  children?: ReactNode;
}) {
  return (
    <div role="alert" className={`flex gap-3 rounded-lg border px-4 py-3 ${STYLES[variant]}`}>
      <span aria-hidden className="select-none font-semibold">{ICON[variant]}</span>
      <div className="text-sm">
        {title && <p className="font-semibold">{title}</p>}
        {children && <div className={title ? "mt-0.5" : ""}>{children}</div>}
      </div>
    </div>
  );
}

export default Alert;
