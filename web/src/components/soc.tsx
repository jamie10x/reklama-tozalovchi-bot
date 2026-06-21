import { clsx } from "clsx";
import { ReactNode } from "react";

export const severityBadge: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

export const statusBadge: Record<string, string> = {
  open: "badge-critical",
  pending: "badge-medium",
  processing: "badge-medium",
  failed: "badge-critical",
  completed: "badge-low",
  claimed: "badge-high",
  confirmed: "badge-medium",
  false_positive: "badge-info",
  escalated: "badge-critical",
  resolved: "badge-low",
  closed: "badge-info",
  in_progress: "badge-high",
  clean: "badge-low",
  advertisement: "badge-high",
  security_threat: "badge-critical",
  ai_review: "badge-medium",
};

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 className="text-2xl font-bold text-surface-900">{title}</h2>
        {description && <p className="mt-1 text-sm text-surface-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function Badge({ value, tone }: { value: string | null | undefined; tone?: string }) {
  const text = value || "unknown";
  return <span className={clsx("badge", tone || statusBadge[text] || severityBadge[text] || "badge-info")}>{text}</span>;
}

export function StatCard({
  label,
  value,
  helper,
  tone = "text-surface-900",
}: {
  label: string;
  value: ReactNode;
  helper?: string;
  tone?: string;
}) {
  return (
    <div className="card min-h-[118px]">
      <p className="stat-label">{label}</p>
      <p className={clsx("stat-value mt-2", tone)}>{value}</p>
      {helper && <p className="mt-2 text-xs text-surface-500">{helper}</p>}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-dashed border-surface-300 bg-surface-50 p-8 text-center">
      <p className="text-sm font-semibold text-surface-800">{title}</p>
      {description && <p className="mx-auto mt-2 max-w-xl text-sm text-surface-500">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
      {message}
    </div>
  );
}

export function SkeletonRows({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-12 animate-pulse rounded bg-surface-100" />
      ))}
    </div>
  );
}

export function RiskMeter({ score }: { score: number }) {
  const width = Math.max(4, Math.min(score, 100));
  const tone =
    score >= 76 ? "bg-red-500" : score >= 51 ? "bg-orange-500" : score >= 21 ? "bg-yellow-500" : "bg-green-500";
  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs text-surface-500">
        <span>Risk</span>
        <span className="font-mono">{score}</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-full bg-surface-100">
        <div className={clsx("h-full rounded-full", tone)} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

export function KeyValue({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-surface-100 py-2 text-sm last:border-b-0">
      <span className="text-surface-500">{label}</span>
      <span className="text-right font-medium text-surface-900">{value}</span>
    </div>
  );
}

export function relativeTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  const diff = Date.now() - date.getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
