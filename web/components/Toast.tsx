"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

type ToastVariant = "success" | "error" | "info";
interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
}

const ToastContext = createContext<{ notify: (m: string, v?: ToastVariant) => void } | null>(null);

const VARIANT_CLASS: Record<ToastVariant, string> = {
  success: "bg-green-600",
  error: "bg-red-600",
  info: "bg-gray-900",
};

/** Wrap the app (or a subtree) to enable useToast(). Auto-dismisses after 3.5s. */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  let counter = 0;

  const notify = useCallback((message: string, variant: ToastVariant = "info") => {
    const id = Date.now() + counter++;
    setToasts((t) => [...t, { id, message, variant }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3500);
  }, []);

  return (
    <ToastContext.Provider value={{ notify }}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4">
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto rounded-full px-4 py-2 text-sm font-medium text-white shadow-lg ${VARIANT_CLASS[t.variant]}`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within a <ToastProvider>");
  return ctx.notify;
}
