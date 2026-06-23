import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  CaptureSettings,
  EnforcementActionType,
  useActivityMessages,
  useCaptureSettings,
  useCreateEnforcementAction,
  useEnforcement,
  useGroup,
  useRetentionStats,
  useUpdateCaptureSettings,
} from "../api/queries";
import { ApiError, downloadApiFile } from "../api/client";
import { Badge, EmptyState, KeyValue, PageHeader, RiskMeter, SkeletonRows, relativeTime } from "../components/soc";
import { useI18n } from "../i18n";

const groupCommands: { action: EnforcementActionType; labelKey: string }[] = [
  { action: "refresh_group_permissions", labelKey: "refresh_permissions" },
  { action: "get_chat_info", labelKey: "get_chat_info" },
  { action: "get_chat_administrators", labelKey: "get_chat_administrators" },
  { action: "get_chat_member_count", labelKey: "get_chat_member_count" },
  { action: "send_recent_messages", labelKey: "send_recent_messages" },
  { action: "save_observed_state", labelKey: "save_observed_state" },
];

export function GroupDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ chatId: string }>();
  const chatId = Number(params.chatId);
  const { data: group, isLoading: groupLoading } = useGroup(chatId);
  const { data: settings } = useCaptureSettings(chatId);
  const { data: retention } = useRetentionStats(chatId);
  const updateSettings = useUpdateCaptureSettings(chatId);
  const command = useCreateEnforcementAction();
  const { data: enforcement, refetch: refetchEnforcement } = useEnforcement({ limit: 5, chat_id: chatId });
  const { data: messages, isLoading: messagesLoading } = useActivityMessages({
    chat_id: chatId,
    limit: 80,
  });
  const [lastCommand, setLastCommand] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const latestCommand = enforcement?.items.find((item) => item.id === lastCommand) ?? (lastCommand ? undefined : enforcement?.items[0]);
  const hasActiveCommand = enforcement?.items.some((item) => item.status === "pending" || item.status === "claimed") ?? false;

  const flagged = useMemo(
    () => messages?.items.filter((item) => item.detection_status !== "clean") ?? [],
    [messages],
  );
  const topSenders = useMemo(() => {
    const counts = new Map<number, { id: number; count: number; flagged: number; username?: string | null }>();
    for (const message of messages?.items ?? []) {
      if (!message.sender_id) continue;
      const current = counts.get(message.sender_id) ?? {
        id: message.sender_id,
        count: 0,
        flagged: 0,
        username: message.sender_username,
      };
      current.count += 1;
      if (message.detection_status !== "clean") current.flagged += 1;
      counts.set(message.sender_id, current);
    }
    return [...counts.values()].sort((a, b) => b.flagged - a.flagged || b.count - a.count).slice(0, 5);
  }, [messages]);

  const setMode = (capture_mode: CaptureSettings["capture_mode"]) => {
    updateSettings.mutate({ capture_mode });
  };

  useEffect(() => {
    if (!hasActiveCommand) return;
    const timer = window.setInterval(() => {
      refetchEnforcement();
    }, 2_000);
    return () => window.clearInterval(timer);
  }, [hasActiveCommand, refetchEnforcement]);

  const runCommand = (action_type: EnforcementActionType) => {
    setOperationError(null);
    command.mutate(
      { action_type, target_chat_id: chatId },
      {
        onSuccess: (action) => {
          setLastCommand(action.id);
          refetchEnforcement();
        },
        onError: (error) => {
          setOperationError(error instanceof ApiError ? error.message : t("command_could_not_queue"));
        },
      },
    );
  };

  const downloadRecent = async () => {
    setOperationError(null);
    try {
      await downloadApiFile(
        `/api/v1/activity/groups/${chatId}/export?limit=200`,
        `observed-messages-${chatId}.json`,
      );
    } catch (error) {
      setOperationError(error instanceof ApiError ? error.message : t("export_failed"));
    }
  };

  return (
    <div>
      <PageHeader
        title={group?.title || `${t("group")} ${chatId}`}
        description={t("group_detail_desc")}
        action={
          <div className="flex gap-2">
            <Link to="/groups" className="btn-secondary">
              {t("back_to_groups")}
            </Link>
            <Link to={`/activity?chat_id=${chatId}`} className="btn-primary">
              {t("open_activity")}
            </Link>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">{t("bot_capability")}</h3>
            </div>
            {groupLoading ? (
              <SkeletonRows rows={4} />
            ) : group ? (
              <div>
                <KeyValue label="Chat ID" value={<span className="font-mono">{group.telegram_chat_id}</span>} />
                <KeyValue label={t("username")} value={group.username ? `@${group.username}` : "-"} />
                <KeyValue label={t("protection_mode")} value={<Badge value={group.mode} />} />
                <KeyValue label={t("group_enabled")} value={<Badge value={group.enabled ? t("enabled") : t("disabled")} />} />
                <KeyValue
                  label={t("delete_messages")}
                  value={<Badge value={group.bot_can_delete_messages ? t("ready") : t("missing")} tone={group.bot_can_delete_messages ? "badge-low" : "badge-critical"} />}
                />
              </div>
            ) : (
              <EmptyState title={t("group_not_found")} description={t("group_not_found_desc")} />
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">{t("capture_policy")}</h3>
                <p className="text-xs text-surface-500">{t("capture_policy_desc")}</p>
              </div>
              <Badge value={settings?.enabled ? "enabled" : "disabled"} />
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(["metadata_only", "flagged_only", "full_text"] as const).map((mode) => (
                <button
                  key={mode}
                  className={settings?.capture_mode === mode ? "btn-primary px-2" : "btn-secondary px-2"}
                  disabled={updateSettings.isPending}
                  onClick={() => setMode(mode)}
                >
                  {mode.replace("_", " ")}
                </button>
              ))}
            </div>
            <p className="mt-3 text-xs text-surface-500">
              {t("full_text_policy_note")}
            </p>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="text-xs font-medium text-surface-500">
                {t("metadata_retention_days")}
                <input
                  className="input mt-1"
                  type="number"
                  min={1}
                  max={3650}
                  value={settings?.metadata_retention_days ?? 30}
                  onChange={(event) => updateSettings.mutate({ metadata_retention_days: Number(event.target.value) })}
                />
              </label>
              <label className="text-xs font-medium text-surface-500">
                {t("flagged_retention_days")}
                <input
                  className="input mt-1"
                  type="number"
                  min={1}
                  max={3650}
                  value={settings?.flagged_retention_days ?? 90}
                  onChange={(event) => updateSettings.mutate({ flagged_retention_days: Number(event.target.value) })}
                />
              </label>
            </div>
            {retention && (
              <div className="mt-4 rounded-lg border border-surface-200 bg-surface-50 p-3 text-xs text-surface-600">
                {t("stored_text_messages")}: {retention.stored_text_messages ?? 0} / {t("retention_total")}: {retention.total_messages ?? 0}
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">{t("group_commands")}</h3>
            </div>
	            <p className="mb-3 text-xs text-surface-500">{t("export_recent_messages_desc")}</p>
	            <div className="grid gap-2">
                  <button className="btn-primary justify-start" type="button" onClick={downloadRecent}>
                    {t("download_recent_json")}
                  </button>
	              {groupCommands.map((item) => (
                <button
                  key={item.action}
                  className="btn-secondary justify-start"
                  disabled={command.isPending}
                  onClick={() => runCommand(item.action)}
                >
                  {t(item.labelKey)}
                </button>
              ))}
            </div>
            {latestCommand && (
              <div className="mt-4 rounded-lg border border-surface-200 bg-surface-50 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-surface-900">{latestCommand.action_type}</p>
                    <p className="font-mono text-xs text-surface-500">{latestCommand.id}</p>
                  </div>
                  <Badge value={latestCommand.status} />
                </div>
                {(latestCommand.status === "pending" || latestCommand.status === "claimed") && (
                  <p className="mt-2 text-xs text-surface-500">
                    {t("waiting_bot_worker")}
                  </p>
                )}
                {latestCommand.result && (
                  <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-surface-950 p-3 text-xs text-white">
                    {JSON.stringify(latestCommand.result, null, 2)}
                  </pre>
                )}
                <Link to="/commands" className="btn-secondary mt-3 w-full px-2 py-1.5">
                  {t("open_full_result_window")}
                </Link>
              </div>
            )}
            {(command.error || operationError) && <p className="mt-3 text-sm text-red-700">{operationError || t("command_could_not_queue")}</p>}
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="card">
              <p className="stat-label">{t("observed_messages")}</p>
              <p className="stat-value mt-2">{messages?.total ?? 0}</p>
            </div>
            <div className="card">
              <p className="stat-label">{t("flagged_messages")}</p>
              <p className="stat-value mt-2 text-orange-600">{flagged.length}</p>
            </div>
            <div className="card">
              <p className="stat-label">{t("last_activity")}</p>
              <p className="mt-3 text-lg font-semibold text-surface-900">
                {relativeTime(messages?.items[0]?.created_at)}
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">{t("recent_activity")}</h3>
              <Link to="/monitor" className="link text-sm">
                {t("live_triage_link")}
              </Link>
            </div>
            {messagesLoading ? (
              <SkeletonRows rows={6} />
            ) : messages?.items.length ? (
              <div className="space-y-3">
                {messages.items.slice(0, 12).map((message) => (
                  <div key={message.id} className="rounded-lg border border-surface-200 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge value={message.detection_status} />
                          <span className="font-mono text-xs text-surface-400">msg={message.message_id}</span>
                          <span className="text-xs text-surface-500">{relativeTime(message.created_at)}</span>
                        </div>
                        <p className="mt-2 text-sm text-surface-800">
                          {message.text || (message.has_text ? t("capture_policy_hidden") : t("no_message_text"))}
                        </p>
                        <p className="mt-1 font-mono text-xs text-surface-500">
                          user={message.sender_id ?? "-"} {message.sender_username ? `@${message.sender_username}` : ""}
                        </p>
                      </div>
                      <div className="w-32 shrink-0">
                        <RiskMeter score={message.risk_score} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title={t("no_data_yet")}
                description={t("old_history_limit")}
              />
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">{t("top_observed_members")}</h3>
            </div>
            {topSenders.length ? (
              <div className="space-y-3">
                {topSenders.map((sender) => (
                  <Link
                    key={sender.id}
                    to={`/members-osint?telegram_id=${sender.id}`}
                    className="flex items-center justify-between rounded-lg border border-surface-200 p-3 hover:bg-surface-50"
                  >
                    <div>
                      <p className="font-mono text-sm font-semibold text-surface-900">{sender.id}</p>
                      <p className="text-xs text-surface-500">{sender.username ? `@${sender.username}` : t("no_username")}</p>
                    </div>
                    <div className="text-right text-xs text-surface-500">
                      <p>{sender.count} {t("messages")}</p>
                      <p>{sender.flagged} {t("flagged")}</p>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title={t("no_member_activity")} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
