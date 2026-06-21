import { Link } from "react-router-dom";
import { useLiveActivity } from "../api/queries";

const badge: Record<string, string> = {
  security_threat: "badge-critical",
  advertisement: "badge-high",
  ai_review: "badge-medium",
  clean: "badge-low",
};

export function LiveMonitorPage() {
  const { data, isLoading } = useLiveActivity();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Live Monitor</h2>
        <p className="mt-1 text-sm text-surface-500">
          Real-time feed for messages that need security attention
        </p>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="h-24 animate-pulse rounded bg-surface-100" />
        ) : (
          <div className="space-y-3">
            {data?.items.map((message) => (
              <div key={message.id} className="rounded-lg border border-surface-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-surface-500">
                      chat={message.chat_id} msg={message.message_id} user={message.sender_id || "-"}
                    </p>
                    <p className="mt-1 text-sm font-medium text-surface-900">
                      {message.sender_username ? `@${message.sender_username}` : "Unknown sender"}
                    </p>
                  </div>
                  <span className={`badge ${badge[message.detection_status] || "badge-info"}`}>
                    {message.detection_status}
                  </span>
                </div>
                <p className="mt-3 rounded bg-surface-50 p-3 text-sm text-surface-800">
                  {message.text || "Text hidden by capture policy"}
                </p>
                <div className="mt-3 flex items-center justify-between text-xs text-surface-500">
                  <span>{new Date(message.created_at).toLocaleString("uz-UZ")}</span>
                  {message.event_id && (
                    <Link to={`/events/${message.event_id}`} className="link">
                      Open event
                    </Link>
                  )}
                </div>
              </div>
            ))}
            {data?.items.length === 0 && (
              <p className="text-sm text-surface-500">No suspicious messages captured yet.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
