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
import { useI18n } from "../i18n";

const filters = [
  { value: "", labelKey: "all" },
  { value: "security_threat", labelKey: "security_threat" },
  { value: "advertisement", labelKey: "advertisement" },
  { value: "ai_review", labelKey: "ai_review" },
  { value: "clean", labelKey: "clean" },
];

export function LiveMonitorPage() {
  const { t } = useI18n();
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
        title={t("live_triage")}
        description={t("live_triage_desc")}
        action={
          <div className="flex gap-2">
            <Link to="/activity" className="btn-secondary">
              {t("activity_store")}
            </Link>
            <Link to="/commands" className="btn-primary">
              {t("bot_commands")}
            </Link>
          </div>
        }
      />

      <div className="card mb-6 grid gap-4 md:grid-cols-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-500">{t("group")}</label>
          <select
            className="input"
            value={chatId ?? ""}
            onChange={(event) => setChatId(event.target.value ? Number(event.target.value) : undefined)}
          >
            <option value="">{t("all_groups")}</option>
            {groups?.items.map((group) => (
              <option key={group.telegram_chat_id} value={group.telegram_chat_id}>
                {group.title || group.telegram_chat_id}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-surface-500">{t("status")}</label>
          <select className="input" value={status} onChange={(event) => setStatus(event.target.value)}>
            {filters.map((filter) => (
              <option key={filter.value} value={filter.value}>
                {t(filter.labelKey)}
              </option>
            ))}
          </select>
        </div>
        <div className="rounded-lg border border-surface-200 p-3">
          <p className="text-xs font-medium uppercase text-surface-500">{t("queue")}</p>
          <p className="mt-1 text-2xl font-bold text-surface-900">{messages.length}</p>
          <p className="text-xs text-surface-500">{t("auto_refresh_5s")}</p>
        </div>
      </div>

      {lastAction && <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">{lastAction}</div>}
      {(command.error || createCase.error) && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {t("action_queue_failed")}
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
                          {t("delete_message")}
                        </button>
                        <button
                          className="btn-secondary px-2"
                          disabled={command.isPending || !message.sender_id}
                          onClick={() => runCommand(message, "trust_sender")}
                        >
                          {t("trust_sender")}
                        </button>
                        <button
                          className="btn-secondary px-2"
                          disabled={command.isPending || !message.sender_id}
                          onClick={() => runCommand(message, "mute_member")}
                        >
                          {t("mute_member")}
                        </button>
                        <button
                          className="btn-danger px-2"
                          disabled={command.isPending || !message.sender_id}
                          onClick={() => runCommand(message, "ban_member")}
                        >
                          {t("ban_member")}
                        </button>
                      </div>
                      <button
                        className="btn-primary w-full"
                        disabled={createCase.isPending}
                        onClick={() => escalate(message)}
                      >
                        {t("case_created")}
                      </button>
                  </div>
                }
              />
            ))}
          </div>
        ) : (
          <EmptyState
            title={t("no_live_triage")}
            description={t("no_live_triage_desc")}
            action={<Link to="/groups" className="btn-secondary">{t("group_health")}</Link>}
          />
        )}
      </div>
    </div>
  );
}
