import { Link } from "react-router-dom";
import { useDashboard, useEnforcement, useEvents, useGroups, useLiveActivity } from "../api/queries";
import { Badge, EmptyState, PageHeader, RiskMeter, SkeletonRows, StatCard, relativeTime } from "../components/soc";

function permissionTone(canDelete: boolean) {
  return canDelete ? "badge-low" : "badge-critical";
}

export function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboard();
  const { data: groups, isLoading: groupsLoading } = useGroups();
  const { data: live } = useLiveActivity();
  const { data: openEvents } = useEvents({ limit: 6, status: "open" });
  const { data: failedCommands } = useEnforcement({ limit: 5, status: "failed" });
  const groupsWithoutDelete =
    groups?.items.filter((group) => group.enabled && !group.bot_can_delete_messages) ?? [];
  const criticalQueue =
    openEvents?.items.filter((event) => event.severity === "critical" || event.severity === "high") ?? [];
  const avgPermissionScore = groups?.items.length
    ? Math.round(
        (groups.items.filter((group) => group.bot_can_delete_messages).length / groups.items.length) * 100,
      )
    : 0;

  return (
    <div>
      <PageHeader
        title="Command Center"
        description="Operational view for authorized Telegram group monitoring, evidence capture, and bot response."
        action={
          <div className="flex gap-2">
            <Link to="/monitor" className="btn-primary">
              Open triage
            </Link>
            <Link to="/commands" className="btn-secondary">
              Queue command
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Open events"
          value={statsLoading ? <span className="inline-block h-8 w-14 animate-pulse rounded bg-surface-200" /> : stats?.open_events ?? 0}
          helper={`${criticalQueue.length} high-priority in queue`}
          tone="text-red-600"
        />
        <StatCard
          label="Active groups"
          value={statsLoading ? <span className="inline-block h-8 w-14 animate-pulse rounded bg-surface-200" /> : stats?.active_groups ?? 0}
          helper={`${groupsWithoutDelete.length} need delete permission`}
          tone="text-surface-900"
        />
        <StatCard
          label="Live flags"
          value={live?.items.length ?? 0}
          helper="Auto-refreshing every 5 seconds"
          tone="text-orange-600"
        />
        <StatCard
          label="Permission readiness"
          value={`${avgPermissionScore}%`}
          helper="Groups where deletion is available"
          tone={avgPermissionScore >= 80 ? "text-green-600" : "text-orange-600"}
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Attention Queue</h3>
              <p className="text-xs text-surface-500">Open high-risk events and live suspicious messages</p>
            </div>
            <Link to="/events" className="link text-sm">
              View all
            </Link>
          </div>

          {criticalQueue.length === 0 && (live?.items.length ?? 0) === 0 ? (
            <EmptyState
              title="No high-priority items right now"
              description="When the bot detects phishing, scam, illegal goods, or severe spam indicators, they will appear here first."
            />
          ) : (
            <div className="space-y-3">
              {criticalQueue.map((event) => (
                <Link
                  key={event.id}
                  to={`/events/${event.id}`}
                  className="block rounded-lg border border-surface-200 p-4 hover:border-surface-300 hover:bg-surface-50"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge value={event.severity} />
                        <Badge value={event.event_type} />
                        <span className="font-mono text-xs text-surface-400">#{event.event_number}</span>
                      </div>
                      <p className="mt-2 text-sm font-semibold text-surface-900">
                        {event.title || event.message_excerpt || "Untitled event"}
                      </p>
                      <p className="mt-1 font-mono text-xs text-surface-500">
                        chat={event.chat_id} user={event.sender_id ?? "-"} msg={event.message_id ?? "-"}
                      </p>
                    </div>
                    <div className="w-36 shrink-0">
                      <RiskMeter score={event.score} />
                    </div>
                  </div>
                </Link>
              ))}
              {live?.items.slice(0, 3).map((message) => (
                <Link
                  key={message.id}
                  to="/monitor"
                  className="block rounded-lg border border-orange-200 bg-orange-50/50 p-4 hover:bg-orange-50"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <Badge value={message.detection_status} />
                      <p className="mt-2 text-sm font-medium text-surface-900">
                        {message.text || "Text hidden by capture policy"}
                      </p>
                      <p className="mt-1 font-mono text-xs text-surface-500">
                        chat={message.chat_id} user={message.sender_id ?? "-"}
                      </p>
                    </div>
                    <span className="text-xs text-surface-500">{relativeTime(message.created_at)}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <div>
                <h3 className="card-title">Group Permission Health</h3>
                <p className="text-xs text-surface-500">Bot capability status by group</p>
              </div>
              <Link to="/groups" className="link text-sm">
                Manage
              </Link>
            </div>
            {groupsLoading ? (
              <SkeletonRows rows={4} />
            ) : groups?.items.length ? (
              <div className="space-y-3">
                {groups.items.slice(0, 6).map((group) => (
                  <Link
                    key={group.telegram_chat_id}
                    to={`/groups/${group.telegram_chat_id}`}
                    className="flex items-center justify-between gap-3 rounded-lg border border-surface-200 p-3 hover:bg-surface-50"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-surface-900">
                        {group.title || group.telegram_chat_id}
                      </p>
                      <p className="font-mono text-xs text-surface-500">{group.telegram_chat_id}</p>
                    </div>
                    <span className={`badge ${permissionTone(group.bot_can_delete_messages)}`}>
                      {group.bot_can_delete_messages ? "ready" : "limited"}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState
                title="No groups registered"
                description="Add the bot to a Telegram group and send a message so the bot can observe the group."
              />
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Failed Commands</h3>
            </div>
            {failedCommands?.items.length ? (
              <div className="space-y-3">
                {failedCommands.items.map((action) => (
                  <div key={action.id} className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium text-red-900">{action.action_type}</span>
                      <Badge value={action.status} />
                    </div>
                    <p className="mt-1 font-mono text-xs text-red-700">
                      chat={action.target_chat_id ?? "-"} user={action.target_user_id ?? "-"}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No failed bot actions" description="Telegram API command failures will be surfaced here." />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
