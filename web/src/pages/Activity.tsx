import { useMemo, useState } from "react";
import {
  CaptureSettings,
  useActivityMessages,
  useCaptureSettings,
  useGroups,
  useUpdateCaptureSettings,
} from "../api/queries";

export function ActivityPage() {
  const { data: groups } = useGroups();
  const [chatId, setChatId] = useState<number | undefined>(undefined);
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

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Group Activity</h2>
        <p className="mt-1 text-sm text-surface-500">
          Stored future message metadata and flagged evidence
        </p>
      </div>

      <div className="card mb-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">Group</label>
            <select
              className="input"
              value={chatId ?? ""}
              onChange={(event) =>
                setChatId(event.target.value ? Number(event.target.value) : undefined)
              }
            >
              <option value="">All groups</option>
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
            Flagged only
          </label>
        </div>

        <div className="rounded-lg border border-surface-200 p-3">
          <p className="text-xs font-medium uppercase text-surface-500">Capture mode</p>
          <p className="mt-1 text-sm font-semibold text-surface-900">
            {selectedGroup?.title || (chatId ? chatId : "Select group")}
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
        </div>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-12 animate-pulse rounded bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="pb-3 font-medium">Time</th>
                  <th className="pb-3 font-medium">Chat</th>
                  <th className="pb-3 font-medium">Message</th>
                  <th className="pb-3 font-medium">Sender</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Text</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((message) => (
                  <tr key={message.id} className="border-b border-surface-100 align-top">
                    <td className="py-3 text-xs text-surface-500">
                      {new Date(message.created_at).toLocaleString("uz-UZ")}
                    </td>
                    <td className="py-3 font-mono text-xs">{message.chat_id}</td>
                    <td className="py-3 font-mono text-xs">{message.message_id}</td>
                    <td className="py-3">
                      {message.sender_username ? `@${message.sender_username}` : message.sender_id || "-"}
                    </td>
                    <td className="py-3">
                      <span className="badge badge-info">{message.detection_status}</span>
                    </td>
                    <td className="max-w-xl py-3 text-surface-700">
                      {message.text || (message.has_text ? "Hidden by policy" : "-")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
