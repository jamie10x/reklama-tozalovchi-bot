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
  useUpdateCaptureSettings,
} from "../api/queries";
import { Badge, EmptyState, KeyValue, PageHeader, RiskMeter, SkeletonRows, relativeTime } from "../components/soc";

const groupCommands: { action: EnforcementActionType; label: string }[] = [
  { action: "refresh_group_permissions", label: "Refresh permissions" },
  { action: "get_chat_info", label: "Get chat info" },
  { action: "get_chat_administrators", label: "Get admins" },
  { action: "get_chat_member_count", label: "Member count" },
  { action: "save_observed_state", label: "Save state" },
];

export function GroupDetailPage() {
  const params = useParams<{ chatId: string }>();
  const chatId = Number(params.chatId);
  const { data: group, isLoading: groupLoading } = useGroup(chatId);
  const { data: settings } = useCaptureSettings(chatId);
  const updateSettings = useUpdateCaptureSettings(chatId);
  const command = useCreateEnforcementAction();
  const { data: enforcement, refetch: refetchEnforcement } = useEnforcement({ limit: 5, chat_id: chatId });
  const { data: messages, isLoading: messagesLoading } = useActivityMessages({
    chat_id: chatId,
    limit: 80,
  });
  const [lastCommand, setLastCommand] = useState<string | null>(null);
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
    command.mutate(
      { action_type, target_chat_id: chatId },
      {
        onSuccess: (action) => {
          setLastCommand(action.id);
          refetchEnforcement();
        },
      },
    );
  };

  return (
    <div>
      <PageHeader
        title={group?.title || `Group ${chatId}`}
        description="Operational profile for bot permissions, capture policy, observed messages, and response commands."
        action={
          <div className="flex gap-2">
            <Link to="/groups" className="btn-secondary">
              Back to groups
            </Link>
            <Link to={`/activity?chat_id=${chatId}`} className="btn-primary">
              Open activity
            </Link>
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Bot Capability</h3>
            </div>
            {groupLoading ? (
              <SkeletonRows rows={4} />
            ) : group ? (
              <div>
                <KeyValue label="Chat ID" value={<span className="font-mono">{group.telegram_chat_id}</span>} />
                <KeyValue label="Username" value={group.username ? `@${group.username}` : "-"} />
                <KeyValue label="Protection mode" value={<Badge value={group.mode} />} />
                <KeyValue label="Group enabled" value={<Badge value={group.enabled ? "enabled" : "disabled"} />} />
                <KeyValue
                  label="Delete messages"
                  value={<Badge value={group.bot_can_delete_messages ? "ready" : "missing"} tone={group.bot_can_delete_messages ? "badge-low" : "badge-critical"} />}
                />
              </div>
            ) : (
              <EmptyState title="Group not found" description="The public bot database has no matching group row." />
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Capture Policy</h3>
                <p className="text-xs text-surface-500">Controls what future messages can store</p>
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
              Full text should be used only when the group owner authorizes evidence retention.
            </p>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Group Commands</h3>
            </div>
            <div className="grid gap-2">
              {groupCommands.map((item) => (
                <button
                  key={item.action}
                  className="btn-secondary justify-start"
                  disabled={command.isPending}
                  onClick={() => runCommand(item.action)}
                >
                  {item.label}
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
                    Waiting for the bot worker. This card refreshes automatically.
                  </p>
                )}
                {latestCommand.result && (
                  <pre className="mt-3 max-h-64 overflow-auto rounded-lg bg-surface-950 p-3 text-xs text-white">
                    {JSON.stringify(latestCommand.result, null, 2)}
                  </pre>
                )}
                <Link to="/commands" className="btn-secondary mt-3 w-full px-2 py-1.5">
                  Open full result window
                </Link>
              </div>
            )}
            {command.error && <p className="mt-3 text-sm text-red-700">Command could not be queued.</p>}
          </div>
        </div>

        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="card">
              <p className="stat-label">Observed messages</p>
              <p className="stat-value mt-2">{messages?.total ?? 0}</p>
            </div>
            <div className="card">
              <p className="stat-label">Flagged messages</p>
              <p className="stat-value mt-2 text-orange-600">{flagged.length}</p>
            </div>
            <div className="card">
              <p className="stat-label">Last activity</p>
              <p className="mt-3 text-lg font-semibold text-surface-900">
                {relativeTime(messages?.items[0]?.created_at)}
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Recent Activity</h3>
              <Link to="/monitor" className="link text-sm">
                Live triage
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
                          {message.text || (message.has_text ? "Text hidden by capture policy" : "No message text")}
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
                title="No observed messages yet"
                description="The bot only captures messages it receives after being added to the group. If the group is quiet, this panel stays empty."
              />
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Top Observed Members</h3>
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
                      <p className="text-xs text-surface-500">{sender.username ? `@${sender.username}` : "No username"}</p>
                    </div>
                    <div className="text-right text-xs text-surface-500">
                      <p>{sender.count} messages</p>
                      <p>{sender.flagged} flagged</p>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState title="No member activity yet" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
