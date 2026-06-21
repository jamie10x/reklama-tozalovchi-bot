import { FormEvent, useState } from "react";
import {
  EnforcementActionType,
  useCreateEnforcementAction,
  useEnforcement,
  useGroups,
} from "../api/queries";

const actions: { value: EnforcementActionType; label: string }[] = [
  { value: "refresh_group_permissions", label: "Guruh ruxsatlarini tekshirish" },
  { value: "delete_message", label: "Xabarni o'chirish" },
  { value: "refresh_member", label: "A'zoni tekshirish" },
  { value: "trust_sender", label: "A'zoni ishonchli qilish" },
  { value: "restrict_member", label: "A'zoni cheklash" },
  { value: "mute_member", label: "A'zoni 1 soat mute qilish" },
  { value: "ban_member", label: "A'zoni ban qilish" },
];

function parseOptionalInt(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function CommandsPage() {
  const { data: groups } = useGroups();
  const { data: enforcement } = useEnforcement({ limit: 20 });
  const createAction = useCreateEnforcementAction();
  const [actionType, setActionType] = useState<EnforcementActionType>("refresh_group_permissions");
  const [chatId, setChatId] = useState("");
  const [messageId, setMessageId] = useState("");
  const [userId, setUserId] = useState("");
  const [result, setResult] = useState<string | null>(null);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    createAction.mutate(
      {
        action_type: actionType,
        target_chat_id: parseOptionalInt(chatId),
        target_message_id: parseOptionalInt(messageId),
        target_user_id: parseOptionalInt(userId),
      },
      {
        onSuccess: (action) => setResult(`${action.action_type}: ${action.status}`),
      },
    );
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Bot buyruqlari</h2>
        <p className="mt-1 text-sm text-surface-500">
          Admin paneldan bot bajaradigan Telegram amallarini navbatga qo'yish
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px]">
        <form onSubmit={submit} className="card space-y-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">Buyruq</label>
            <select
              className="input"
              value={actionType}
              onChange={(event) => setActionType(event.target.value as EnforcementActionType)}
            >
              {actions.map((action) => (
                <option key={action.value} value={action.value}>
                  {action.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-xs font-medium text-surface-500">Guruh</label>
            <select className="input" value={chatId} onChange={(event) => setChatId(event.target.value)}>
              <option value="">Chat ID qo'lda kiritiladi</option>
              {groups?.items.map((group) => (
                <option key={group.telegram_chat_id} value={group.telegram_chat_id}>
                  {group.title || group.telegram_chat_id} ({group.telegram_chat_id})
                </option>
              ))}
            </select>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">Chat ID</label>
              <input className="input" value={chatId} onChange={(event) => setChatId(event.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">Message ID</label>
              <input className="input" value={messageId} onChange={(event) => setMessageId(event.target.value)} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-500">User ID</label>
              <input className="input" value={userId} onChange={(event) => setUserId(event.target.value)} />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="btn-primary" disabled={createAction.isPending}>
              Buyruq yuborish
            </button>
            {result && <span className="text-sm text-green-700">{result}</span>}
            {createAction.error && <span className="text-sm text-red-700">Buyruq rad etildi</span>}
          </div>
        </form>

        <div className="card">
          <h3 className="card-title mb-4">So'nggi buyruqlar</h3>
          <div className="space-y-3">
            {enforcement?.items.map((item) => (
              <div key={item.id} className="rounded-lg border border-surface-200 p-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-medium">{item.action_type}</span>
                  <span className="badge badge-info">{item.status}</span>
                </div>
                <p className="mt-1 font-mono text-xs text-surface-500">
                  chat={item.target_chat_id || "-"} user={item.target_user_id || "-"} msg={item.target_message_id || "-"}
                </p>
                {item.result && (
                  <pre className="mt-2 max-h-24 overflow-auto rounded bg-surface-900 p-2 text-xs text-white">
                    {JSON.stringify(item.result, null, 2)}
                  </pre>
                )}
              </div>
            ))}
            {enforcement?.items.length === 0 && (
              <p className="text-sm text-surface-500">Hali buyruqlar yo'q</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
