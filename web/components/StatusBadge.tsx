export type ApplicationStatus = "draft" | "submitted" | "approved" | "rejected";

const META: Record<ApplicationStatus, { label: string; className: string }> = {
  draft: { label: "Draft", className: "bg-gray-100 text-gray-700 ring-gray-200" },
  submitted: { label: "Submitted", className: "bg-blue-50 text-blue-700 ring-blue-200" },
  approved: { label: "Approved", className: "bg-green-50 text-green-700 ring-green-200" },
  rejected: { label: "Rejected", className: "bg-red-50 text-red-700 ring-red-200" },
};

/** A small, accessible status pill for tracked applications. */
export function StatusBadge({ status }: { status: ApplicationStatus }) {
  const m = META[status] ?? META.draft;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${m.className}`}
      aria-label={`Status: ${m.label}`}
    >
      {m.label}
    </span>
  );
}

export default StatusBadge;
