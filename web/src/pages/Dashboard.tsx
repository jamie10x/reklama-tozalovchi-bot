import { Link } from "react-router-dom";
import { useDashboard, useEnforcement, useEvents, useGroups, useLiveActivity } from "../api/queries";
import { Badge, EmptyState, PageHeader, RiskMeter, SkeletonRows, StatCard, relativeTime } from "../components/soc";
import { useI18n } from "../i18n";

function permissionTone(canDelete: boolean) {
  return canDelete ? "badge-low" : "badge-critical";
}

export function DashboardPage() {
  const { t } = useI18n();
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
        title={t("command_center")}
        description={t("dashboard_description")}
        action={
          <div className="flex gap-2">
            <Link to="/monitor" className="btn-primary">
              {t("open_triage")}
            </Link>
            <Link to="/commands" className="btn-secondary">
              {t("queue_command")}
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={t("open_events")}
          value={statsLoading ? <span className="inline-block h-8 w-14 animate-pulse rounded bg-surface-200" /> : stats?.open_events ?? 0}
          helper={`${criticalQueue.length} ${t("high_priority_queue")}`}
          tone="text-red-600"
        />
        <StatCard
          label={t("active_groups")}
          value={statsLoading ? <span className="inline-block h-8 w-14 animate-pulse rounded bg-surface-200" /> : stats?.active_groups ?? 0}
          helper={`${groupsWithoutDelete.length} ${t("need_delete_permission")}`}
          tone="text-surface-900"
        />
        <StatCard
          label={t("live_flags")}
          value={live?.items.length ?? 0}
          helper={t("auto_refresh_5s")}
          tone="text-orange-600"
        />
        <StatCard
          label={t("permission_readiness")}
          value={`${avgPermissionScore}%`}
          helper={t("deletion_available_groups")}
          tone={avgPermissionScore >= 80 ? "text-green-600" : "text-orange-600"}
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(360px,0.75fr)]">
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">{t("attention_queue")}</h3>
              <p className="text-xs text-surface-500">{t("attention_queue_desc")}</p>
            </div>
            <Link to="/events" className="link text-sm">
              {t("view_all")}
            </Link>
          </div>

          {criticalQueue.length === 0 && (live?.items.length ?? 0) === 0 ? (
            <EmptyState
              title={t("no_priority_title")}
              description={t("no_priority_desc")}
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
                        {event.title || event.message_excerpt || t("untitled_event")}
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
                        {message.text || t("capture_policy_hidden")}
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
                <h3 className="card-title">{t("group_permission_health")}</h3>
                <p className="text-xs text-surface-500">{t("group_permission_desc")}</p>
              </div>
              <Link to="/groups" className="link text-sm">
                {t("manage")}
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
                      {group.bot_can_delete_messages ? t("ready") : t("limited")}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <EmptyState
                title={t("no_groups_visible")}
                description={t("no_groups_desc")}
              />
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">{t("failed_commands")}</h3>
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
              <EmptyState title={t("no_failed_actions")} description={t("failed_actions_desc")} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
