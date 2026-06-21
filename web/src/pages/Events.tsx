import { useState } from "react";
import { Link } from "react-router-dom";
import { useEvents } from "../api/queries";
import { useDebounce } from "../hooks/useDebounce";

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
        <h2 className="text-2xl font-bold text-surface-900">Voqealar</h2>
        <p className="mt-1 text-sm text-surface-500">
          Bot aniqlagan oxirgi 200 ta xavfsizlik va reklama voqealari
        </p>
      </div>

      <div className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input"
            >
              <option value="">Barchasi</option>
              <option value="open">Ochiq</option>
              <option value="claimed">Qabul qilingan</option>
              <option value="confirmed">Tasdiqlangan</option>
              <option value="escalated">Escalated</option>
              <option value="resolved">Hal qilingan</option>
              <option value="false_positive">False positive</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Daraja</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="input"
            >
              <option value="">Barchasi</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Tur</label>
            <select
              value={eventType}
              onChange={(e) => setEventType(e.target.value)}
              className="input"
            >
              <option value="">Barchasi</option>
              <option value="advertisement">Reklama</option>
              <option value="security_threat">Security threat</option>
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
                  <th className="pb-3 font-medium">Tur</th>
                  <th className="pb-3 font-medium">Daraja</th>
                  <th className="pb-3 font-medium">Ball</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Vaqt</th>
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
                        Batafsil
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
