import { useParams } from "react-router-dom";
import { useEvent } from "../api/queries";

const severityBadge: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

const statusBadge: Record<string, string> = {
  open: "badge-critical",
  investigating: "badge-high",
  resolved: "badge-low",
  dismissed: "badge-info",
};

export function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: event, isLoading } = useEvent(id!);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-surface-200" />
        <div className="h-64 animate-pulse rounded-xl bg-surface-100" />
      </div>
    );
  }

  if (!event) {
    return (
      <div className="card text-center text-surface-500">
        Voqea topilmadi
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">
          Voqea #{event.event_number}
        </h2>
        <p className="mt-1 text-sm text-surface-500">
          {event.title || "Sarlavhasiz voqea"}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="card-title mb-4">Asosiy ma'lumot</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-surface-500">Tur</dt>
              <dd className="font-medium capitalize">{event.event_type}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Daraja</dt>
              <dd>
                <span className={`badge ${severityBadge[event.severity]}`}>
                  {event.severity}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Ball</dt>
              <dd className="font-mono font-medium">{event.score}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Status</dt>
              <dd>
                <span className={`badge ${statusBadge[event.status]}`}>
                  {event.status}
                </span>
              </dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">Tafsilotlar</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-surface-500">Chat ID</dt>
              <dd className="font-mono">{event.chat_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Xabar ID</dt>
              <dd className="font-mono">{event.message_id || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Yuboruvchi ID</dt>
              <dd className="font-mono">{event.sender_id || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Yaratilgan</dt>
              <dd>{new Date(event.created_at).toLocaleString("uz-UZ")}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">Yangilangan</dt>
              <dd>{new Date(event.updated_at).toLocaleString("uz-UZ")}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
