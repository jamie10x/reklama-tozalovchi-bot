import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  EnforcementActionType,
  ObservedMessage,
  useCreateCase,
  useCreateEnforcementAction,
  useGroups,
  useLiveActivity,
} from "../api/queries";
import { EmptyState, MessageInfoCard, PageHeader, SkeletonRows } from "../components/soc";

const filters = [
  { value: "", label: "All statuses" },
  { value: "security_threat", label: "Security threat" },
  { value: "advertisement", label: "Advertisement" },
  { value: "ai_review", label: "AI review" },
  { value: "clean", label: "Clean" },
];

export function LiveMonitorPage() {
  const { data: groups } = useGroups();
  const [chatId, setChatId] = useState<number | undefined>();
  const [status, setStatus] = useState("");
  const { data, isLoading } = useLiveActivity(chatId);
  const command = useCreateEnforcementAction();
  const createCase = useCreateCase();
  const [lastAction, setLastAction] = useState<string | null>(null);

  const messages = useMemo(
    () => (data?.items ?? []).filter((message) => !status || message.detection_status === status),
    [data, status],
  );

  const runCommand = (message: ObservedMessage, action_type: EnforcementActionType) => {
    command.mutate(
      {
        action_type,
        target_chat_id: message.chat_id,
        target_message_id: action_type === "delete_message" ? message.message_id : undefined,
        target_user_id:
          action_type === "delete_message" || action_type === "refresh_group_permissions"
            ? undefined
            : message.sender_id,
      },
      {
        onSuccess: (action) => setLastAction(`${action.action_type}: ${action.status}`),
      },
    );
  };

  const escalate = (message: ObservedMessage) => {
    createCase.mutate(
      {
        title: `Telegram ${message.detection_status} in ${message.chat_id}`,
        severity: message.risk_score >= 76 ? "critical" : message.risk_score >= 51 ? "high" : "medium",
        description: [
          `Chat ID: ${message.chat_id}`,
          `Message ID: ${message.message_id}`,
          `Sender ID: ${message.sender_id ?? "-"}`,
          `Risk score: ${message.risk_score}`,
          `Status: ${message.detection_status}`,
          `Text: ${message.text || "Hidden by capture policy"}`,
        ].join("\n"),
      },
      {
        onSuccess: (item) => setLastAction(`case #${item.case_number}: created`),
      },
    );
  };

  return (
    <div>
      <PageHeader
        title="Live Triage"
        description="Auto-refreshing queue for suspicious Telegram activity and rapid response commands."
        action={
          <div className="flex gap-2">
            <Link to="/activity" className="btn-secondary">
              Activity store
            </Link>
            <Link to="/commands" className="btn-primary">
              Command console
            </Link>
          </div>
        }
      />

      <div className="card mb-6 grid gap-4 md:grid-cols-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-500">Group</label>
          <select
            className="input"
            value={chatId ?? ""}
            onChange={(event) => setChatId(event.target.value ? Number(event.target.value) : undefined)}
          >
            <option value="">All groups</option>
            {groups?.items.map((group) => (
              <option key={group.telegram_chat_id} value={group.telegram_chat_id}>
                {group.title || group.telegram_chat_id}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-500">Status</label>
          <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
            {filters.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {filter.label}
              </option>
            ))}
          </select>
        </div>
        <div className="rounded-lg border border-surface-200 p-3">
          <p className="text-xs font-medium uppercase text-surface-500">Queue</p>
          <p className="mt-1 text-2xl font-bold text-surface-900">{messages.length}</p>
          <p className="text-xs text-surface-500">refreshes every 5 seconds</p>
        </div>
      </div>

      {lastAction && <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">{lastAction}</div>}
      {(command.error || createCase.error) && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Action could not be queued. Check target IDs and bot permissions.
        </div>
      )}

      <div className="card">
        {isLoading ? (
          <SkeletonRows rows={6} />
        ) : messages.length ? (
          <div className="space-y-4">
            {messages.map((message) => (
              <MessageInfoCard
                key={message.id}
                message={message}
                action={
                  <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          className="btn-danger px-2"
                          disabled={command.isPending}
                          onClick={() => runCommand(message, "delete_message")}
                        >
                          Delete
                        </button>
                        <button
                          className="btn-secondary px-2"
                          disabled={command.isPending || !message.sender_id}
                          onClick={() => runCommand(message, "trust_sender")}
                        >
                          Trust
                        </button>
                        <button
                          className="btn-secondary px-2"
                          disabled={command.isPending || !message.sender_id}
                          onClick={() => runCommand(message, "mute_member")}
                        >
                          Mute
                        </button>
                        <button
                          className="btn-danger px-2"
                          disabled={command.isPending || !message.sender_id}
                          onClick={() => runCommand(message, "ban_member")}
                        >
                          Ban
                        </button>
                      </div>
                      <button
                        className="btn-primary w-full"
                        disabled={createCase.isPending}
                        onClick={() => escalate(message)}
                      >
                        Create case
                      </button>
                  </div>
                }
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title="No live triage items"
            description="Flagged messages appear here after the bot receives future group updates. Clean messages are stored in Activity if capture settings allow it."
            action={<Link to="/groups" className="btn-secondary">Check group health</Link>}
          />
        )}
      </div>
    </div>
  );
}
