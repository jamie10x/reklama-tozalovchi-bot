import { useState } from "react";
import { Link } from "react-router-dom";
import { useEvents } from "../api/queries";
import { useDebounce } from "../hooks/useDebounce";
import { useI18n } from "../i18n";

const severityBadge: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

const statusBadge: Record<string, string> = {
  open: "badge-critical",
  claimed: "badge-high",
  confirmed: "badge-medium",
  false_positive: "badge-info",
  escalated: "badge-critical",
  resolved: "badge-low",
};

export function EventsPage() {
  const { t } = useI18n();
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");
  const [eventType, setEventType] = useState("");
  const debouncedStatus = useDebounce(status, 300);
  const debouncedSeverity = useDebounce(severity, 300);
  const debouncedType = useDebounce(eventType, 300);

  const { data, isLoading } = useEvents({
    limit: 200,
    status: debouncedStatus || undefined,
    severity: debouncedSeverity || undefined,
    event_type: debouncedType || undefined,
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("events")}</h2>
        <p className="mt-1 text-sm text-surface-500">
          {t("events_desc")}
        </p>
      </div>

      <div className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("status")}</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input"
            >
              <option value="">{t("all")}</option>
              <option value="open">{t("open")}</option>
              <option value="claimed">{t("claimed")}</option>
              <option value="confirmed">{t("confirmed")}</option>
              <option value="escalated">{t("escalated")}</option>
              <option value="resolved">{t("resolved")}</option>
              <option value="false_positive">{t("false_positive")}</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("severity")}</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="input"
            >
              <option value="">{t("all")}</option>
              <option value="critical">{t("critical")}</option>
              <option value="high">{t("high")}</option>
              <option value="medium">{t("medium")}</option>
              <option value="low">{t("low")}</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("type")}</label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="input"
            >
              <option value="">{t("all")}</option>
              <option value="advertisement">{t("advertisement")}</option>
              <option value="security_threat">{t("security_threat")}</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="pb-3 font-medium">#</th>
                  <th className="pb-3 font-medium">{t("type")}</th>
                  <th className="pb-3 font-medium">{t("severity")}</th>
                  <th className="pb-3 font-medium">{t("score")}</th>
                  <th className="pb-3 font-medium">{t("status")}</th>
                  <th className="pb-3 font-medium">{t("time")}</th>
                  <th className="pb-3 font-medium" />
                </tr>
              </thead>
              <tbody>
                {data?.items.map((event) => (
                  <tr key={event.id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 font-mono text-xs">{event.event_number}</td>
                    <td className="py-3 capitalize">{event.event_type}</td>
                    <td className="py-3">
                      <span className={`badge ${severityBadge[event.severity] || "badge-info"}`}>
                        {event.severity}
                      </span>
                    </td>
                    <td className="py-3 font-mono">{event.score}</td>
                    <td className="py-3">
                      <span className={`badge ${statusBadge[event.status] || "badge-info"}`}>
                        {event.status}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-surface-500">
                      {new Date(event.created_at).toLocaleString("uz-UZ")}
                    </td>
                    <td className="py-3">
                      <Link to={`/events/${event.id}`} className="link text-xs">
                        {t("details")}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
