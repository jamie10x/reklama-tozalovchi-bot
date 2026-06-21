import { FormEvent, useState } from "react";
import {
  EnforcementActionType,
  useCreateEnforcementAction,
  useEnforcement,
  useGroups,
} from "../api/queries";
import { Badge, EmptyState, PageHeader } from "../components/soc";

const actions: {
  value: EnforcementActionType;
  label: string;
  scope: "group" | "message" | "member" | "intel";
  requires: string;
}[] = [
  { value: "refresh_group_permissions", label: "Refresh permissions", scope: "group", requires: "Chat ID" },
  { value: "get_chat_info", label: "Get chat info", scope: "intel", requires: "Chat ID" },
  { value: "get_chat_administrators", label: "Get administrators", scope: "intel", requires: "Chat ID" },
  { value: "get_chat_member_count", label: "Get member count", scope: "intel", requires: "Chat ID" },
  { value: "save_observed_state", label: "Save observed state", scope: "group", requires: "Chat ID" },
  { value: "delete_message", label: "Delete message", scope: "message", requires: "Chat ID + Message ID" },
  { value: "refresh_member", label: "Refresh member", scope: "member", requires: "Chat ID + User ID" },
  { value: "trust_sender", label: "Trust sender", scope: "member", requires: "Chat ID + User ID" },
  { value: "restrict_member", label: "Restrict member", scope: "member", requires: "Chat ID + User ID" },
  { value: "mute_member", label: "Mute member for 1 hour", scope: "member", requires: "Chat ID + User ID" },
  { value: "ban_member", label: "Ban member", scope: "member", requires: "Chat ID + User ID" },
  { value: "get_user_profile_photos", label: "Profile photo metadata", scope: "intel", requires: "User ID" },
];

function parseOptionalInt(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function CommandsPage() {
  const { data: groups } = useGroups();
  const { data: enforcement } = useEnforcement({ limit: 20 });
  const createAction = useCreateEnforcementAction();
  const [actionType, setActionType] = useState<EnforcementActionType>("refresh_group_permissions");
  const [chatId, setChatId] = useState("");
  const [messageId, setMessageId] = useState("");
  const [userId, setUserId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const selectedAction = actions.find((action) => action.value === actionType) ?? actions[0];

  const submit = (event: FormEvent) => {
    event.preventDefault();
    createAction.mutate(
      {
        action_type: actionType,
        target_chat_id: parseOptionalInt(chatId),
        target_message_id: parseOptionalInt(messageId),
        target_user_id: parseOptionalInt(userId),
      },
      {
        onSuccess: (action) => setResult(`${action.action_type}: ${action.status}`),
      },
    );
  };

  return (
    <div>
      <PageHeader
        title="Bot Commands"
        description="Queue Telegram Bot API actions. Commands execute only where the bot has authorized access and permissions."
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <form onSubmit={submit} className="card space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {actions.slice(0, 4).map((action) => (
              <button
                key={action.value}
                type="button"
                className={actionType === action.value ? "btn-primary justify-start px-3" : "btn-secondary justify-start px-3"}
                onClick={() => setActionType(action.value)}
              >
                {action.label}
              </button>
            ))}
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">Command</label>
            <select
              className="input"
              value={actionType}
              onChange={(event) => setActionType(event.target.value as EnforcementActionType)}
            >
              {actions.map((action) => (
                <option key={action.value} value={action.value}>
                  {action.label}
                </option>
              ))}
            </select>
          </div>

          <div className="rounded-lg border border-surface-200 bg-surface-50 p-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-surface-900">{selectedAction.label}</p>
                <p className="text-xs text-surface-500">Required: {selectedAction.requires}</p>
              </div>
              <Badge value={selectedAction.scope} />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">Group</label>
            <select className="input" value={chatId} onChange={(event) => setChatId(event.target.value)}>
              <option value="">Manual Chat ID</option>
              {groups?.items.map((group) => (
                <option key={group.telegram_chat_id} value={group.telegram_chat_id}>
                  {group.title || group.telegram_chat_id} ({group.telegram_chat_id})
                </option>
              ))}
            </select>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">Chat ID</label>
              <input className="input" value={chatId} onChange={(event) => setChatId(event.target.value)} placeholder="-100..." />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">Message ID</label>
              <input className="input" value={messageId} onChange={(event) => setMessageId(event.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">User ID</label>
              <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="btn-primary" disabled={createAction.isPending}>
              Queue command
            </button>
            {result && <span className="text-sm text-green-700">{result}</span>}
            {createAction.error && <span className="text-sm text-red-700">Command rejected</span>}
          </div>
        </form>

        <div className="card">
          <h3 className="card-title mb-4">Recent commands</h3>
          <div className="space-y-3">
            {enforcement?.items.map((item) => (
              <div key={item.id} className="rounded-lg border border-surface-200 p-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{item.action_type}</span>
                  <Badge value={item.status} />
                </div>
                <p className="mt-1 font-mono text-xs text-surface-500">
                  chat={item.target_chat_id || "-"} user={item.target_user_id || "-"} msg={item.target_message_id || "-"}
                </p>
                {item.result && (
                  <pre className="mt-2 max-h-24 overflow-auto rounded bg-surface-900 p-2 text-xs text-white">
                    {JSON.stringify(item.result, null, 2)}
                  </pre>
                )}
              </div>
            ))}
            {enforcement?.items.length === 0 && (
              <EmptyState title="No commands queued yet" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
