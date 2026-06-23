import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ObservedMessage, useCreateEnforcementAction, useUserIntel } from "../api/queries";
import {
  Badge,
  EmptyState,
  KeyValue,
  MessageInfoCard,
  PageHeader,
  RiskMeter,
  SkeletonRows,
  StatCard,
  relativeTime,
} from "../components/soc";
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
  cross_group_activity?: Array<{
    chat_id: number;
    message_count: number;
    flagged_count: number;
    last_seen_at: string | null;
  }>;
  timeline?: Array<Record<string, unknown> & { type: string; created_at?: string | null }>;
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

  const runMemberCommand = (chatId: number) => {
    if (!intel?.user) return;
    command.mutate(
      {
        action_type: "refresh_member",
        target_chat_id: chatId,
        target_user_id: intel.user.telegram_id,
      },
      { onSuccess: (action) => setLastAction(`${action.action_type}: ${action.status}`) },
    );
  };

  return (
    <div>
      <PageHeader title={t("member_intel")} description={t("member_intel_desc")} />

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
            {t("activity_store")}
          </Link>
        </div>
        <p className="mt-2 text-xs text-surface-500">{t("osint_scope_note")}</p>
      </div>

      {lastAction && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700">
          {lastAction}
        </div>
      )}
      {command.error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {t("command_could_not_queue")}
        </div>
      )}

      {isLoading && (
        <div className="card">
          <SkeletonRows rows={5} />
        </div>
      )}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {t("intel_lookup_failed")}
        </div>
      )}
      {!validId && <EmptyState title={t("enter_telegram_user_id")} description={t("open_member_prefill")} />}

      {intel?.user && validId && (
        <div className="grid gap-6 xl:grid-cols-[360px_minmax(0,1fr)]">
          <div className="space-y-6">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("member_profile")}</h3>
              </div>
              <KeyValue label="ID" value={<span className="font-mono">{intel.user.telegram_id}</span>} />
              <KeyValue label={t("username")} value={intel.user.current_username ? `@${intel.user.current_username}` : "-"} />
              <KeyValue
                label={t("name")}
                value={[intel.user.current_first_name, intel.user.current_last_name].filter(Boolean).join(" ") || "-"}
              />
              <KeyValue label={t("first_seen")} value={relativeTime(intel.user.first_seen_at)} />
              <KeyValue label={t("last_seen")} value={relativeTime(intel.user.last_seen_at)} />
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
                    onClick={() => runMemberCommand(intel.profiles?.[0]?.chat_id as number)}
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
                        {alias.username ? `@${alias.username}` : t("no_username")}
                      </p>
                      <p className="text-xs text-surface-500">
                        {[alias.first_name, alias.last_name].filter(Boolean).join(" ") || t("no_display_name")}
                      </p>
                      <p className="mt-1 text-xs text-surface-400">
                        {t("last_seen")} {relativeTime(alias.last_seen_at)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title={t("no_alias_history")} />
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="grid gap-4 md:grid-cols-3">
              <StatCard label={t("group_profiles")} value={totals.groups} helper={`${totals.messages} ${t("observed_messages").toLowerCase()}`} />
              <StatCard label={t("events")} value={totals.events} helper={`${totals.deleted} ${t("deleted_messages")}`} tone={totals.events ? "text-red-700" : "text-surface-900"} />
              <StatCard label={t("risk_signals")} value={totals.signals} helper={`${totals.aliases} ${t("aliases_recorded")}`} tone={totals.signals ? "text-orange-700" : "text-surface-900"} />
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
                        <span>{profile.message_count ?? 0} {t("messages")}</span>
                        <span>{profile.security_event_count ?? 0} {t("events")}</span>
                        <span>{profile.deleted_message_count ?? 0} {t("deleted_messages")}</span>
                        <span>{t("last_seen")} {relativeTime(profile.last_message_at)}</span>
                      </div>
                      <div className="mt-3 grid gap-2 sm:grid-cols-2">
                        <Link to={`/groups/${profile.chat_id}`} className="btn-secondary px-2 py-1.5">
                          {t("open_operations")}
                        </Link>
                        <button
                          className="btn-secondary px-2 py-1.5"
                          disabled={command.isPending}
                          onClick={() => runMemberCommand(profile.chat_id)}
                        >
                          {t("refresh_member")}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title={t("no_group_profiles")} />
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("cross_group_activity")}</h3>
              </div>
              {intel.cross_group_activity?.length ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {intel.cross_group_activity.map((row) => (
                    <Link key={row.chat_id} to={`/groups/${row.chat_id}`} className="rounded-lg border border-surface-200 p-4 hover:bg-surface-50">
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-mono text-sm font-semibold text-surface-900">{row.chat_id}</span>
                        <Badge value={`${row.flagged_count} ${t("flagged")}`} />
                      </div>
                      <p className="mt-2 text-xs text-surface-500">
                        {row.message_count} {t("messages")} / {t("last_seen")} {relativeTime(row.last_seen_at)}
                      </p>
                    </Link>
                  ))}
                </div>
              ) : (
                <EmptyState title={t("no_cross_group_activity")} />
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">{t("member_timeline")}</h3>
              </div>
              {intel.timeline?.length ? (
                <div className="space-y-3">
                  {intel.timeline.slice(0, 30).map((item, index) => (
                    <div key={index} className="rounded-lg border border-surface-200 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <Badge value={item.type} />
                        <span className="text-xs text-surface-500">{relativeTime(item.created_at)}</span>
                      </div>
                      <pre className="mt-2 max-h-32 overflow-auto rounded-lg bg-surface-50 p-2 text-xs text-surface-700">
                        {JSON.stringify(item, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title={t("no_member_timeline")} />
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
                <EmptyState title={t("no_risk_signals")} />
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
                <EmptyState title={t("no_member_messages")} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
