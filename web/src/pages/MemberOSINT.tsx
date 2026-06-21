import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ObservedMessage, useCreateEnforcementAction, useUserIntel } from "../api/queries";
import { Badge, EmptyState, KeyValue, MessageInfoCard, PageHeader, RiskMeter, SkeletonRows, StatCard, relativeTime } from "../components/soc";
import { useI18n } from "../i18n";

type IntelResponse = {
  user?: {
    telegram_id: number;
    current_username: string | null;
    current_first_name: string | null;
    current_last_name: string | null;
    risk_score: number;
    first_seen_at: string | null;
    last_seen_at: string | null;
  };
  profiles?: Array<{
    chat_id: number;
    membership_status?: string;
    is_admin?: boolean;
    message_count?: number;
    link_message_count?: number;
    deleted_message_count?: number;
    security_event_count?: number;
    confirmed_event_count?: number;
    last_message_at?: string | null;
    last_security_event_at?: string | null;
  }>;
  aliases?: Array<{
    username?: string | null;
    first_name?: string | null;
    last_name?: string | null;
    first_seen_at?: string | null;
    last_seen_at?: string | null;
  }>;
  risk_signals?: Array<{
    chat_id?: number | null;
    signal_type?: string;
    signal_value?: string;
    detected_at?: string | null;
    created_at?: string | null;
  }>;
  messages?: ObservedMessage[];
};

export function MemberOSINTPage() {
  const { t } = useI18n();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialId = searchParams.get("telegram_id") ?? "";
  const [rawId, setRawId] = useState(initialId);
  const telegramId = rawId.trim() ? Number(rawId.trim()) : undefined;
  const validId = Number.isFinite(telegramId) ? telegramId : undefined;
  const { data, isLoading, error } = useUserIntel(validId);
  const command = useCreateEnforcementAction();
  const [lastAction, setLastAction] = useState<string | null>(null);
  const intel = data as IntelResponse | undefined;
  const totals = {
    groups: intel?.profiles?.length ?? 0,
    messages: intel?.profiles?.reduce((sum, profile) => sum + (profile.message_count ?? 0), 0) ?? 0,
    events: intel?.profiles?.reduce((sum, profile) => sum + (profile.security_event_count ?? 0), 0) ?? 0,
    deleted: intel?.profiles?.reduce((sum, profile) => sum + (profile.deleted_message_count ?? 0), 0) ?? 0,
    aliases: intel?.aliases?.length ?? 0,
    signals: intel?.risk_signals?.length ?? 0,
  };

  const updateRawId = (value: string) => {
    setRawId(value);
    const next = new URLSearchParams(searchParams);
    if (value.trim()) next.set("telegram_id", value.trim());
    else next.delete("telegram_id");
    setSearchParams(next, { replace: true });
  };

  return (
    <div>
      <PageHeader
        title={t("member_intel")}
        description="Telegram-only profile built from data the bot is authorized to observe in groups."
      />

      <div className="card mb-6">
        <label className="mb-1 block text-xs font-medium text-surface-500">{t("telegram_user_id")}</label>
        <div className="flex max-w-xl gap-2">
          <input
            className="input"
            value={rawId}
            onChange={(event) => updateRawId(event.target.value)}
            placeholder="660089656"
          />
          <Link to="/activity" className="btn-secondary">
            Activity
          </Link>
        </div>
        <p className="mt-2 text-xs text-surface-500">
          OSINT here means Telegram-only observations from authorized groups. It does not query private Telegram history.
        </p>
      </div>

      {lastAction && <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">{lastAction}</div>}
      {command.error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Bot command could not be queued. Check target IDs and group permissions.
        </div>
      )}

      {isLoading && (
        <div className="card">
          <SkeletonRows rows={5} />
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Intel lookup failed. Check the user ID and API authentication.
        </div>
      )}

      {!validId && (
        <EmptyState title="Enter a Telegram user ID" description="Open a member from Activity or Group Operations to prefill this page." />
      )}

      {intel?.user && validId && (
        <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("member_profile")}</h3>
              </div>
              <KeyValue label="ID" value={<span className="font-mono">{intel.user.telegram_id}</span>} />
              <KeyValue label="Username" value={intel.user.current_username ? `@${intel.user.current_username}` : "-"} />
              <KeyValue
                label="Name"
                value={[intel.user.current_first_name, intel.user.current_last_name].filter(Boolean).join(" ") || "-"}
              />
              <KeyValue label="First seen" value={relativeTime(intel.user.first_seen_at)} />
              <KeyValue label="Last seen" value={relativeTime(intel.user.last_seen_at)} />
              <div className="mt-4">
                <RiskMeter score={intel.user.risk_score} />
              </div>
              <div className="mt-4 grid gap-2">
                <button
                  className="btn-secondary w-full"
                  disabled={command.isPending}
                  onClick={() =>
                    command.mutate(
                      { action_type: "get_user_profile_photos", target_user_id: intel.user?.telegram_id },
                      { onSuccess: (action) => setLastAction(`${action.action_type}: ${action.status}`) },
                    )
                  }
                >
                  {t("fetch_profile_photos")}
                </button>
                {intel.profiles?.[0]?.chat_id && (
                  <button
                    className="btn-secondary w-full"
                    disabled={command.isPending}
                    onClick={() =>
                      command.mutate(
                        {
                          action_type: "refresh_member",
                          target_chat_id: intel.profiles?.[0]?.chat_id,
                          target_user_id: intel.user?.telegram_id,
                        },
                        { onSuccess: (action) => setLastAction(`${action.action_type}: ${action.status}`) },
                      )
                    }
                  >
                    {t("refresh_member")}
                  </button>
                )}
              </div>
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("aliases")}</h3>
              </div>
              {intel.aliases?.length ? (
                <div className="space-y-3">
                  {intel.aliases.map((alias, index) => (
                    <div key={index} className="rounded-lg border border-surface-200 p-3">
                      <p className="text-sm font-semibold text-surface-900">
                        {alias.username ? `@${alias.username}` : "No username"}
                      </p>
                      <p className="text-xs text-surface-500">
                        {[alias.first_name, alias.last_name].filter(Boolean).join(" ") || "No display name"}
                      </p>
                      <p className="mt-1 text-xs text-surface-400">last seen {relativeTime(alias.last_seen_at)}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No alias history yet" />
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
              <StatCard label="Groups" value={totals.groups} helper={`${totals.messages} observed messages`} />
              <StatCard label="Events" value={totals.events} helper={`${totals.deleted} deleted messages`} tone={totals.events ? "text-red-700" : "text-surface-900"} />
              <StatCard label="Signals" value={totals.signals} helper={`${totals.aliases} aliases recorded`} tone={totals.signals ? "text-orange-700" : "text-surface-900"} />
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("group_profiles")}</h3>
              </div>
              {intel.profiles?.length ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {intel.profiles.map((profile) => (
                    <div key={profile.chat_id} className="rounded-lg border border-surface-200 p-4">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm font-semibold text-surface-900">{profile.chat_id}</span>
                        <Badge value={profile.is_admin ? "admin" : profile.membership_status || "member"} />
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-surface-500">
                        <span>{profile.message_count ?? 0} messages</span>
                        <span>{profile.security_event_count ?? 0} events</span>
                        <span>{profile.deleted_message_count ?? 0} deleted</span>
                        <span>last {relativeTime(profile.last_message_at)}</span>
                      </div>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        <Link to={`/groups/${profile.chat_id}`} className="btn-secondary px-2 py-1.5">
                          Open group
                        </Link>
                        <button
                          className="btn-secondary px-2 py-1.5"
                          disabled={command.isPending}
                          onClick={() =>
                            command.mutate(
                            {
                              action_type: "refresh_member",
                              target_chat_id: profile.chat_id,
                              target_user_id: intel.user?.telegram_id,
                            },
                            { onSuccess: (action) => setLastAction(`${action.action_type}: ${action.status}`) },
                            )
                          }
                        >
                          {t("refresh_member")}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No group profiles yet" />
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("risk_signals")}</h3>
              </div>
              {intel.risk_signals?.length ? (
                <div className="space-y-3">
                  {intel.risk_signals.map((signal, index) => (
                    <div key={index} className="rounded-lg border border-surface-200 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <Badge value={signal.signal_type} />
                        <span className="font-mono text-xs text-surface-500">{signal.chat_id ?? "-"}</span>
                      </div>
                      <p className="mt-2 text-sm text-surface-800">{signal.signal_value || "-"}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No risk signals yet" />
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("recent_observed_messages")}</h3>
              </div>
              {intel.messages?.length ? (
                <div className="space-y-3">
                  {intel.messages.map((message) => (
                    <MessageInfoCard key={message.id} message={message} compact />
                  ))}
                </div>
              ) : (
                <EmptyState title="No observed messages for this member yet" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
