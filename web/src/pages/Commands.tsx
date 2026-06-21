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
  labelKey: string;
  scope: "group" | "message" | "member" | "intel";
  requiresKey: string;
}[] = [
  { value: "refresh_group_permissions", labelKey: "refresh_permissions", scope: "group", requiresKey: "chat_id" },
  { value: "get_chat_info", labelKey: "get_chat_info", scope: "intel", requiresKey: "chat_id" },
  { value: "get_chat_administrators", labelKey: "get_chat_administrators", scope: "intel", requiresKey: "chat_id" },
  { value: "get_chat_member_count", labelKey: "get_chat_member_count", scope: "intel", requiresKey: "chat_id" },
  { value: "send_recent_messages", labelKey: "send_recent_messages", scope: "intel", requiresKey: "chat_id" },
  { value: "save_observed_state", labelKey: "save_observed_state", scope: "group", requiresKey: "chat_id" },
  { value: "delete_message", labelKey: "delete_message", scope: "message", requiresKey: "chat_message_id" },
  { value: "refresh_member", labelKey: "refresh_member", scope: "member", requiresKey: "chat_user_id" },
  { value: "trust_sender", labelKey: "trust_sender", scope: "member", requiresKey: "chat_user_id" },
  { value: "restrict_member", labelKey: "restrict_member", scope: "member", requiresKey: "chat_user_id" },
  { value: "mute_member", labelKey: "mute_member", scope: "member", requiresKey: "chat_user_id" },
  { value: "ban_member", labelKey: "ban_member", scope: "member", requiresKey: "chat_user_id" },
  { value: "get_user_profile_photos", labelKey: "fetch_profile_photos", scope: "intel", requiresKey: "user_id" },
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

function summarizeResult(result: Record<string, unknown> | null, t: (key: string) => string) {
  if (!result) return [];
  const chat = result.chat as Record<string, unknown> | undefined;
  const pinned = chat?.pinned_message as Record<string, unknown> | undefined;
  const permissions = chat?.permissions as Record<string, unknown> | undefined;
  const administrators = result.administrators as unknown[] | undefined;
  const photos = result.photos as unknown[] | undefined;
  const rows: Array<[string, unknown]> = [];

  if (chat) {
    rows.push([t("title"), chat.title]);
    rows.push([t("username"), chat.username ? `@${chat.username}` : undefined]);
    rows.push([t("type"), chat.type]);
    rows.push([t("chat_id"), chat.id]);
    rows.push([t("invite"), chat.invite_link]);
    rows.push([t("visible_history"), chat.has_visible_history]);
    rows.push([t("hidden_members"), chat.has_hidden_members]);
    rows.push([t("aggressive_antispam"), chat.has_aggressive_anti_spam_enabled]);
    rows.push([t("permissions"), permissions ? Object.values(permissions).filter(Boolean).length : undefined]);
    rows.push([t("pinned_message"), pinned?.text]);
  }

  if (typeof result.member_count === "number") rows.push([t("member_count"), result.member_count]);
  if (administrators) rows.push([t("administrators"), administrators.length]);
  if (photos) rows.push([t("photo_groups"), photos.length]);
  if (result.status) rows.push([t("status"), result.status]);
  if (result.can_delete_messages !== undefined) rows.push([t("can_delete_messages"), result.can_delete_messages]);
  if (rows.length === 0) {
    Object.entries(result).slice(0, 8).forEach(([key, value]) => rows.push([key, value]));
  }
  return rows.filter(([, value]) => value !== undefined && value !== null);
}

function CommandResultWindow({ item }: { item?: EnforcementAction }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const summary = useMemo(() => summarizeResult(item?.result ?? null, t), [item, t]);
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

      {(item.status === "pending" || item.status === "claimed") && (
        <div className="mb-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-800">
          {t("command_pending_refresh")}
        </div>
      )}
      {item.status === "failed" && item.result && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {t("command_failed_details")}
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)]">
        <div className="space-y-4">
          <div className="rounded-lg border border-surface-200 p-4">
            <p className="mb-2 text-xs font-semibold uppercase text-surface-500">{t("response_metadata")}</p>
            <KeyValue label={t("command")} value={item.action_type} />
            <KeyValue label={t("chat_id")} value={<span className="font-mono">{item.target_chat_id ?? "-"}</span>} />
            <KeyValue label={t("user_id")} value={<span className="font-mono">{item.target_user_id ?? "-"}</span>} />
            <KeyValue label={t("message_id")} value={<span className="font-mono">{item.target_message_id ?? "-"}</span>} />
            <KeyValue label={t("queued")} value={relativeTime(item.created_at)} />
            <KeyValue label={t("completed")} value={relativeTime(item.completed_at)} />
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
  const { data: enforcement, refetch: refetchEnforcement } = useEnforcement({ limit: 20 });
  const createAction = useCreateEnforcementAction();
  const [actionType, setActionType] = useState<EnforcementActionType>("refresh_group_permissions");
  const [chatId, setChatId] = useState("");
  const [messageId, setMessageId] = useState("");
  const [userId, setUserId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedAction = actions.find((action) => action.value === actionType) ?? actions[0];
  const selectedCommand = enforcement?.items.find((item) => item.id === selectedId) ?? (selectedId ? undefined : enforcement?.items[0]);
  const hasActiveCommand = enforcement?.items.some((item) => item.status === "pending" || item.status === "claimed") ?? false;

  useEffect(() => {
    if (!selectedId && enforcement?.items[0]) setSelectedId(enforcement.items[0].id);
  }, [enforcement?.items, selectedId]);

  useEffect(() => {
    if (!hasActiveCommand) return;
    const timer = window.setInterval(() => {
      refetchEnforcement();
    }, 2_000);
    return () => window.clearInterval(timer);
  }, [hasActiveCommand, refetchEnforcement]);

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
        onSuccess: (action) => {
          setSelectedId(action.id);
          setResult(`${action.action_type}: ${action.status}`);
          refetchEnforcement();
        },
      },
    );
  };

  return (
    <div>
      <PageHeader
        title={t("bot_commands")}
        description={t("commands_desc")}
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
                {t(action.labelKey)}
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
                  {t(action.labelKey)}
                </option>
              ))}
            </select>
          </div>

          <div className="rounded-lg border border-surface-200 bg-surface-50 p-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-surface-900">{t(selectedAction.labelKey)}</p>
                <p className="text-xs text-surface-500">{t("required")}: {t(selectedAction.requiresKey)}</p>
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
            {createAction.error && <span className="text-sm text-red-700">{t("command_rejected")}</span>}
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
