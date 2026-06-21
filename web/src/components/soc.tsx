import { clsx } from "clsx";
import { ReactNode } from "react";
import type { ObservedMessage } from "../api/queries";

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

function compactJsonValue(value: unknown) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

export function detectionReasons(message: ObservedMessage) {
  const result = message.detection_result;
  const security = result?.security as { reasons?: string[]; detected_indicators?: Record<string, string[]> } | undefined;
  const ad = result?.ad as { reasons?: string[]; detected_domains?: string[]; detected_telegram_entities?: string[] } | undefined;
  const direct = result?.reasons as string[] | undefined;
  const reasons = [
    ...(direct ?? []),
    ...(security?.reasons ?? []),
    ...(ad?.reasons ?? []),
    ...Object.entries(security?.detected_indicators ?? {}).flatMap(([key, values]) =>
      values.map((value) => `${key}: ${value}`),
    ),
    ...(ad?.detected_domains ?? []).map((item) => `domain: ${item}`),
    ...(ad?.detected_telegram_entities ?? []).map((item) => `telegram: ${item}`),
  ];
  return [...new Set(reasons.filter(Boolean))].slice(0, 10);
}

export function senderName(message: ObservedMessage) {
  const name = [message.sender_first_name, message.sender_last_name].filter(Boolean).join(" ");
  if (message.sender_username) return `@${message.sender_username}`;
  return name || (message.sender_id ? String(message.sender_id) : "Unknown sender");
}

export function MessageInfoCard({
  message,
  action,
  compact = false,
}: {
  message: ObservedMessage;
  action?: ReactNode;
  compact?: boolean;
}) {
  const reasons = detectionReasons(message);
  const scoreRows = [
    ["Ad", message.ad_score],
    ["Security", message.security_score],
    ["AI", message.ai_score],
  ].filter(([, value]) => value !== null && value !== undefined);

  return (
    <div className="rounded-lg border border-surface-200 bg-white p-4">
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_220px]">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge value={message.detection_status} />
            <Badge value={message.message_type} tone="badge-info" />
            {message.is_forwarded && <Badge value="forwarded" tone="badge-medium" />}
            {message.is_edited && <Badge value="edited" tone="badge-medium" />}
            <span className="text-xs text-surface-500">{relativeTime(message.created_at)}</span>
          </div>
          <div className="mt-3 grid gap-2 text-xs text-surface-500 sm:grid-cols-3">
            <span className="font-mono">chat={message.chat_id}</span>
            <span className="font-mono">msg={message.message_id}</span>
            <span className="font-mono">user={message.sender_id ?? "-"}</span>
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span className="font-semibold text-surface-900">{senderName(message)}</span>
            {message.reply_to_message_id && (
              <span className="font-mono text-xs text-surface-500">reply={message.reply_to_message_id}</span>
            )}
          </div>
          <p className={clsx("mt-3 whitespace-pre-wrap rounded-lg bg-surface-50 p-3 text-sm text-surface-800", compact && "line-clamp-4")}>
            {message.text || (message.has_text ? "Text hidden by capture policy" : "No message text")}
          </p>
          {reasons.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {reasons.map((reason) => (
                <span key={reason} className="rounded-full bg-surface-100 px-2 py-1 text-xs text-surface-600">
                  {reason}
                </span>
              ))}
            </div>
          )}
          {!compact && message.detection_result && (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs font-medium text-surface-500">Detection JSON</summary>
              <pre className="mt-2 max-h-56 overflow-auto rounded-lg bg-surface-950 p-3 text-xs text-white">
                {JSON.stringify(message.detection_result, null, 2)}
              </pre>
            </details>
          )}
        </div>
        <div className="space-y-3">
          <RiskMeter score={message.risk_score} />
          {scoreRows.length > 0 && (
            <div className="rounded-lg border border-surface-100 p-3">
              {scoreRows.map(([label, value]) => (
                <KeyValue key={label} label={String(label)} value={<span className="font-mono">{compactJsonValue(value)}</span>} />
              ))}
            </div>
          )}
          {action}
        </div>
      </div>
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
