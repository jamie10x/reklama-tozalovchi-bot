import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  EnforcementAction,
  EnforcementActionType,
  useCreateEnforcementAction,
  useEnforcement,
  useGroups,
} from "../api/queries";
import { Badge, EmptyState, KeyValue, PageHeader, relativeTime } from "../components/soc";
import { useI18n } from "../i18n";

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

function textValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function summarizeResult(result: Record<string, unknown> | null) {
  if (!result) return [];
  const chat = result.chat as Record<string, unknown> | undefined;
  const pinned = chat?.pinned_message as Record<string, unknown> | undefined;
  const permissions = chat?.permissions as Record<string, unknown> | undefined;
  const administrators = result.administrators as unknown[] | undefined;
  const photos = result.photos as unknown[] | undefined;
  const rows: Array<[string, unknown]> = [];

  if (chat) {
    rows.push(["Title", chat.title]);
    rows.push(["Username", chat.username ? `@${chat.username}` : undefined]);
    rows.push(["Type", chat.type]);
    rows.push(["Chat ID", chat.id]);
    rows.push(["Invite", chat.invite_link]);
    rows.push(["Visible history", chat.has_visible_history]);
    rows.push(["Hidden members", chat.has_hidden_members]);
    rows.push(["Aggressive anti-spam", chat.has_aggressive_anti_spam_enabled]);
    rows.push(["Permissions", permissions ? Object.values(permissions).filter(Boolean).length : undefined]);
    rows.push(["Pinned message", pinned?.text]);
  }

  if (typeof result.member_count === "number") rows.push(["Member count", result.member_count]);
  if (administrators) rows.push(["Administrators", administrators.length]);
  if (photos) rows.push(["Photo groups", photos.length]);
  if (result.status) rows.push(["Status", result.status]);
  if (result.can_delete_messages !== undefined) rows.push(["Can delete messages", result.can_delete_messages]);
  if (rows.length === 0) {
    Object.entries(result).slice(0, 8).forEach(([key, value]) => rows.push([key, value]));
  }
  return rows.filter(([, value]) => value !== undefined && value !== null);
}

function CommandResultWindow({ item }: { item?: EnforcementAction }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const summary = useMemo(() => summarizeResult(item?.result ?? null), [item]);
  const json = useMemo(() => JSON.stringify(item?.result ?? {}, null, 2), [item]);

  useEffect(() => setCopied(false), [item?.id]);

  if (!item) {
    return (
      <div className="card flex min-h-[520px] items-center justify-center">
        <EmptyState title={t("select_command_result")} />
      </div>
    );
  }

  const copy = async () => {
    await navigator.clipboard.writeText(json);
    setCopied(true);
  };

  return (
    <div className="card min-h-[520px]">
      <div className="card-header">
        <div>
          <h3 className="card-title">{t("result_window")}</h3>
          <p className="mt-1 font-mono text-xs text-surface-500">{item.id}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge value={item.status} />
          <button type="button" className="btn-secondary px-3 py-1.5" onClick={copy} disabled={!item.result}>
            {copied ? t("copied") : t("copy_json")}
          </button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)]">
        <div className="space-y-4">
          <div className="rounded-lg border border-surface-200 p-4">
            <p className="mb-2 text-xs font-semibold uppercase text-surface-500">{t("response_metadata")}</p>
            <KeyValue label={t("command")} value={item.action_type} />
            <KeyValue label={t("chat_id")} value={<span className="font-mono">{item.target_chat_id ?? "-"}</span>} />
            <KeyValue label={t("user_id")} value={<span className="font-mono">{item.target_user_id ?? "-"}</span>} />
            <KeyValue label={t("message_id")} value={<span className="font-mono">{item.target_message_id ?? "-"}</span>} />
            <KeyValue label="Queued" value={relativeTime(item.created_at)} />
            <KeyValue label="Completed" value={relativeTime(item.completed_at)} />
          </div>

          <div className="rounded-lg border border-surface-200 p-4">
            <p className="mb-2 text-xs font-semibold uppercase text-surface-500">{t("summary")}</p>
            {summary.length ? (
              summary.map(([label, value]) => (
                <KeyValue
                  key={label}
                  label={label}
                  value={<span className="max-w-[170px] truncate">{textValue(value)}</span>}
                />
              ))
            ) : (
              <p className="text-sm text-surface-500">{t("no_data_yet")}</p>
            )}
          </div>
        </div>

        <div className="min-w-0 rounded-lg border border-surface-200 bg-surface-950">
          <div className="flex items-center justify-between border-b border-white/10 px-4 py-2">
            <span className="text-xs font-semibold uppercase text-surface-300">{t("raw_json")}</span>
            <span className="font-mono text-xs text-surface-400">{json.length.toLocaleString()} bytes</span>
          </div>
          <pre className="max-h-[650px] overflow-auto p-4 text-xs leading-relaxed text-white">
            {item.result ? json : t("no_data_yet")}
          </pre>
        </div>
      </div>
    </div>
  );
}

export function CommandsPage() {
  const { t } = useI18n();
  const { data: groups } = useGroups();
  const { data: enforcement } = useEnforcement({ limit: 20 });
  const createAction = useCreateEnforcementAction();
  const [actionType, setActionType] = useState<EnforcementActionType>("refresh_group_permissions");
  const [chatId, setChatId] = useState("");
  const [messageId, setMessageId] = useState("");
  const [userId, setUserId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedAction = actions.find((action) => action.value === actionType) ?? actions[0];
  const selectedCommand = enforcement?.items.find((item) => item.id === selectedId) ?? enforcement?.items[0];

  useEffect(() => {
    if (!selectedId && enforcement?.items[0]) setSelectedId(enforcement.items[0].id);
  }, [enforcement?.items, selectedId]);

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
        title={t("bot_commands")}
        description="Queue Telegram Bot API actions. Commands execute only where the bot has authorized access and permissions."
      />

      <div className="grid gap-6 2xl:grid-cols-[minmax(0,520px)_minmax(0,1fr)]">
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
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("command")}</label>
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
                <p className="text-xs text-surface-500">{t("required")}: {selectedAction.requires}</p>
              </div>
              <Badge value={selectedAction.scope} />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("group")}</label>
            <select className="input" value={chatId} onChange={(event) => setChatId(event.target.value)}>
              <option value="">{t("manual_chat_id")}</option>
              {groups?.items.map((group) => (
                <option key={group.telegram_chat_id} value={group.telegram_chat_id}>
                  {group.title || group.telegram_chat_id} ({group.telegram_chat_id})
                </option>
              ))}
            </select>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">{t("chat_id")}</label>
              <input className="input" value={chatId} onChange={(event) => setChatId(event.target.value)} placeholder="-100..." />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">{t("message_id")}</label>
              <input className="input" value={messageId} onChange={(event) => setMessageId(event.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">{t("user_id")}</label>
              <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="btn-primary" disabled={createAction.isPending}>
              {t("queue_command")}
            </button>
            {result && <span className="text-sm text-green-700">{result}</span>}
            {createAction.error && <span className="text-sm text-red-700">Command rejected</span>}
          </div>
        </form>

        <div className="space-y-6">
          <div className="card">
            <h3 className="card-title mb-4">{t("recent_commands")}</h3>
            <div className="max-h-[360px] space-y-2 overflow-auto pr-1">
              {enforcement?.items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSelectedId(item.id)}
                  className={`w-full rounded-lg border p-3 text-left text-sm transition ${
                    selectedCommand?.id === item.id
                      ? "border-surface-900 bg-surface-50"
                      : "border-surface-200 hover:bg-surface-50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-surface-900">{item.action_type}</span>
                    <Badge value={item.status} />
                  </div>
                  <p className="mt-1 font-mono text-xs text-surface-500">
                    chat={item.target_chat_id || "-"} user={item.target_user_id || "-"} msg={item.target_message_id || "-"}
                  </p>
                  <p className="mt-1 text-xs text-surface-400">{relativeTime(item.created_at)}</p>
                </button>
              ))}
              {enforcement?.items.length === 0 && (
                <EmptyState title={t("no_commands")} />
              )}
            </div>
          </div>
          <CommandResultWindow item={selectedCommand} />
        </div>
      </div>
    </div>
  );
}
