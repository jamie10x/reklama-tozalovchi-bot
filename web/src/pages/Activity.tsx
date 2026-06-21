import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  CaptureSettings,
  useActivityMessages,
  useCaptureSettings,
  useGroups,
  useUpdateCaptureSettings,
} from "../api/queries";
import { EmptyState, MessageInfoCard, PageHeader, SkeletonRows } from "../components/soc";
import { useI18n } from "../i18n";

export function ActivityPage() {
  const { t } = useI18n();
  const { data: groups } = useGroups();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialChatId = searchParams.get("chat_id") ? Number(searchParams.get("chat_id")) : undefined;
  const [chatId, setChatId] = useState<number | undefined>(initialChatId);
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const { data: settings } = useCaptureSettings(chatId);
  const updateSettings = useUpdateCaptureSettings(chatId);
  const { data, isLoading } = useActivityMessages({
    limit: 200,
    chat_id: chatId,
    flagged_only: flaggedOnly,
  });

  const selectedGroup = useMemo(
    () => groups?.items.find((group) => group.telegram_chat_id === chatId),
    [groups, chatId],
  );

  const setMode = (capture_mode: CaptureSettings["capture_mode"]) => {
    updateSettings.mutate({ capture_mode });
  };

  const updateChatId = (value: number | undefined) => {
    setChatId(value);
    const next = new URLSearchParams(searchParams);
    if (value) next.set("chat_id", String(value));
    else next.delete("chat_id");
    setSearchParams(next, { replace: true });
  };

  return (
    <div>
      <PageHeader
        title={t("activity_store")}
        description={t("activity_desc")}
        action={chatId && <Link to={`/groups/${chatId}`} className="btn-secondary">{t("group_operations")}</Link>}
      />

      <div className="card mb-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("group")}</label>
            <select
              className="input"
              value={chatId ?? ""}
              onChange={(event) =>
                updateChatId(event.target.value ? Number(event.target.value) : undefined)
              }
            >
              <option value="">{t("all_groups")}</option>
              {groups?.items.map((group) => (
                <option key={group.telegram_chat_id} value={group.telegram_chat_id}>
                  {group.title || group.telegram_chat_id}
                </option>
              ))}
            </select>
          </div>
          <label className="flex items-end gap-2 text-sm text-surface-700">
            <input
              type="checkbox"
              checked={flaggedOnly}
              onChange={(event) => setFlaggedOnly(event.target.checked)}
            />
            {t("flagged_only")}
          </label>
        </div>

        <div className="rounded-lg border border-surface-200 p-3">
          <p className="text-xs font-medium uppercase text-surface-500">{t("capture_mode")}</p>
          <p className="mt-1 text-sm font-semibold text-surface-900">
            {selectedGroup?.title || (chatId ? chatId : t("select_group"))}
          </p>
          {chatId && (
            <div className="mt-3 grid grid-cols-3 gap-2">
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
          )}
          {!chatId && <p className="mt-2 text-xs text-surface-500">{t("select_group_capture")}</p>}
        </div>
      </div>

      <div className="card">
        {isLoading ? (
          <SkeletonRows rows={6} />
        ) : data?.items.length === 0 ? (
          <EmptyState
            title={t("no_activity_title")}
            description={t("no_activity_desc")}
          />
        ) : (
          <div className="space-y-4">
            {data?.items.map((message) => (
              <MessageInfoCard key={message.id} message={message} compact />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
