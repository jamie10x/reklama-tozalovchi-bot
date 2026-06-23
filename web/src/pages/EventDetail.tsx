import { useState } from "react";
import { useParams } from "react-router-dom";
import {
  EnforcementActionType,
  useCreateEnforcementAction,
  useEvent,
} from "../api/queries";
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

export function EventDetailPage() {
  const { t } = useI18n();
  const { id } = useParams<{ id: string }>();
  const { data: event, isLoading } = useEvent(id!);
  const command = useCreateEnforcementAction();
  const [queuedAction, setQueuedAction] = useState<string | null>(null);

  const queueAction = (actionType: EnforcementActionType) => {
    if (!event) return;
    command.mutate(
      {
        action_type: actionType,
        target_chat_id: event.chat_id,
        target_message_id:
          actionType === "delete_message" ? event.message_id : undefined,
        target_user_id:
          actionType === "refresh_group_permissions" ||
          actionType === "delete_message"
            ? undefined
            : event.sender_id,
      },
      {
        onSuccess: (action) => setQueuedAction(`${action.action_type}: ${action.status}`),
      },
    );
  };

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
        {t("event_not_found")}
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">
          {t("event")} #{event.event_number}
        </h2>
        <p className="mt-1 text-sm text-surface-500">
          {event.title || t("untitled_event")}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="card-title mb-4">{t("basic_info")}</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("type")}</dt>
              <dd className="font-medium capitalize">{event.event_type}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("severity")}</dt>
              <dd>
                <span className={`badge ${severityBadge[event.severity] || "badge-info"}`}>
                  {event.severity}
                </span>
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("score")}</dt>
              <dd className="font-mono font-medium">{event.score}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("status")}</dt>
              <dd>
                <span className={`badge ${statusBadge[event.status] || "badge-info"}`}>
                  {event.status}
                </span>
              </dd>
            </div>
          </dl>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">{t("details")}</h3>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-surface-500">Chat ID</dt>
              <dd className="font-mono">{event.chat_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("message_id")}</dt>
              <dd className="font-mono">{event.message_id || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("sender")} ID</dt>
              <dd className="font-mono">{event.sender_id || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("created")}</dt>
              <dd>{new Date(event.created_at).toLocaleString("uz-UZ")}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-surface-500">{t("updated")}</dt>
              <dd>{new Date(event.updated_at).toLocaleString("uz-UZ")}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="card-title mb-4">{t("message_evidence")}</h3>
          <div className="rounded-lg border border-surface-200 bg-surface-50 p-4 text-sm leading-6 text-surface-800">
            {event.message_excerpt || t("message_text_not_stored")}
          </div>
          <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
            <div>
              <p className="mb-1 text-xs font-medium uppercase text-surface-500">{t("reasons")}</p>
              <pre className="max-h-48 overflow-auto rounded-lg bg-surface-900 p-3 text-xs text-white">
                {JSON.stringify(event.detection_reasons || {}, null, 2)}
              </pre>
            </div>
            <div>
              <p className="mb-1 text-xs font-medium uppercase text-surface-500">{t("indicators")}</p>
              <pre className="max-h-48 overflow-auto rounded-lg bg-surface-900 p-3 text-xs text-white">
                {JSON.stringify(event.detected_indicators || {}, null, 2)}
              </pre>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="card-title mb-4">{t("bot_commands")}</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <button
              className="btn-danger"
              disabled={!event.message_id || command.isPending}
              onClick={() => queueAction("delete_message")}
            >
              {t("delete_message")}
            </button>
            <button
              className="btn-secondary"
              disabled={command.isPending}
              onClick={() => queueAction("refresh_group_permissions")}
            >
              {t("refresh_permissions")}
            </button>
            <button
              className="btn-secondary"
              disabled={!event.sender_id || command.isPending}
              onClick={() => queueAction("refresh_member")}
            >
              {t("refresh_member")}
            </button>
            <button
              className="btn-secondary"
              disabled={!event.sender_id || command.isPending}
              onClick={() => queueAction("trust_sender")}
            >
              {t("trust_sender")}
            </button>
            <button
              className="btn-secondary"
              disabled={!event.sender_id || command.isPending}
              onClick={() => queueAction("mute_member")}
            >
              {t("mute_member")}
            </button>
            <button
              className="btn-danger"
              disabled={!event.sender_id || command.isPending}
              onClick={() => queueAction("ban_member")}
            >
              {t("ban_member")}
            </button>
          </div>
          {queuedAction && (
            <p className="mt-4 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">
              {t("command_queued")}: {queuedAction}
            </p>
          )}
          {command.error && (
            <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {t("command_could_not_queue")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
