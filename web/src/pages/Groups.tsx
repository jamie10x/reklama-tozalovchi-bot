import { Link } from "react-router-dom";
import { useCreateEnforcementAction, useGroups } from "../api/queries";
import { Badge, EmptyState, PageHeader, SkeletonRows } from "../components/soc";

function readiness(group: { enabled: boolean; bot_can_delete_messages: boolean }) {
  if (!group.enabled) return { label: "disabled", tone: "badge-info" };
  if (!group.bot_can_delete_messages) return { label: "limited", tone: "badge-critical" };
  return { label: "ready", tone: "badge-low" };
}

export function GroupsPage() {
  const { data, isLoading, error } = useGroups();
  const command = useCreateEnforcementAction();

  const refresh = (chatId: number) => {
    command.mutate({
      action_type: "refresh_group_permissions",
      target_chat_id: chatId,
    });
  };

  return (
    <div>
      <PageHeader
        title="Group Health"
        description="Bot permissions, protection mode, and operational readiness for every authorized group."
        action={
          <Link to="/commands" className="btn-primary">
            Bot commands
          </Link>
        }
      />

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Group API did not respond. Check nginx/API routing and authentication.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <p className="stat-label">Registered groups</p>
          <p className="stat-value mt-2">{data?.total ?? 0}</p>
        </div>
        <div className="card">
          <p className="stat-label">Ready to moderate</p>
          <p className="stat-value mt-2 text-green-600">
            {data?.items.filter((group) => group.bot_can_delete_messages).length ?? 0}
          </p>
        </div>
        <div className="card">
          <p className="stat-label">Need permission fix</p>
          <p className="stat-value mt-2 text-red-600">
            {data?.items.filter((group) => group.enabled && !group.bot_can_delete_messages).length ?? 0}
          </p>
        </div>
      </div>

      <div className="mt-6 card">
        {isLoading ? (
          <SkeletonRows rows={5} />
        ) : data?.items.length ? (
          <div className="grid gap-4 xl:grid-cols-2">
            {data.items.map((group) => {
              const state = readiness(group);
              return (
                <div key={group.telegram_chat_id} className="rounded-lg border border-surface-200 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="truncate text-base font-semibold text-surface-900">
                          {group.title || "Untitled group"}
                        </h3>
                        <Badge value={state.label} tone={state.tone} />
                      </div>
                      <p className="mt-1 font-mono text-xs text-surface-500">{group.telegram_chat_id}</p>
                      {group.username && <p className="mt-1 text-xs text-surface-500">@{group.username}</p>}
                    </div>
                    <Badge value={group.mode} />
                  </div>

                  <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                    <div className="rounded-lg bg-surface-50 p-3">
                      <p className="text-xs text-surface-500">Monitoring</p>
                      <p className="mt-1 font-semibold text-surface-900">{group.enabled ? "Enabled" : "Disabled"}</p>
                    </div>
                    <div className="rounded-lg bg-surface-50 p-3">
                      <p className="text-xs text-surface-500">Delete permission</p>
                      <p className="mt-1 font-semibold text-surface-900">{group.bot_can_delete_messages ? "Available" : "Missing"}</p>
                    </div>
                    <div className="rounded-lg bg-surface-50 p-3">
                      <p className="text-xs text-surface-500">Added</p>
                      <p className="mt-1 font-semibold text-surface-900">
                        {new Date(group.created_at).toLocaleDateString("uz-UZ")}
                      </p>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link to={`/groups/${group.telegram_chat_id}`} className="btn-primary">
                      Open operations
                    </Link>
                    <button
                      className="btn-secondary"
                      disabled={command.isPending}
                      onClick={() => refresh(group.telegram_chat_id)}
                    >
                      Refresh permissions
                    </button>
                    <Link to={`/activity?chat_id=${group.telegram_chat_id}`} className="btn-ghost">
                      Activity
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            title="No groups visible"
            description="If the bot is already in a Telegram group, send a test message there and refresh permissions. Telegram history cannot be imported retroactively."
            action={<Link to="/commands" className="btn-secondary">Open bot commands</Link>}
          />
        )}
      </div>
    </div>
  );
}
