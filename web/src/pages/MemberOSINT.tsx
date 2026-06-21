import { useState } from "react";
import { useUserIntel } from "../api/queries";

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
  profiles?: Array<Record<string, unknown>>;
  aliases?: Array<Record<string, unknown>>;
  risk_signals?: Array<Record<string, unknown>>;
  messages?: Array<Record<string, unknown>>;
};

export function MemberOSINTPage() {
  const [rawId, setRawId] = useState("");
  const telegramId = rawId.trim() ? Number(rawId.trim()) : undefined;
  const { data, isLoading, error } = useUserIntel(Number.isFinite(telegramId) ? telegramId : undefined);
  const intel = data as IntelResponse | undefined;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Members OSINT</h2>
        <p className="mt-1 text-sm text-surface-500">
          Telegram-only intelligence from data visible to the bot
        </p>
      </div>

      <div className="card mb-6">
        <label className="mb-1 block text-xs font-medium text-surface-500">Telegram user ID</label>
        <input
          className="input max-w-sm"
          value={rawId}
          onChange={(event) => setRawId(event.target.value)}
          placeholder="660089656"
        />
      </div>

      {isLoading && <div className="card">Loading...</div>}
      {error && <div className="card text-red-700">No observed profile found for this ID.</div>}

      {intel?.user && (
        <div className="grid gap-6 xl:grid-cols-2">
          <div className="card">
            <h3 className="card-title mb-4">Profile</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-surface-500">ID</dt>
                <dd className="font-mono">{intel.user.telegram_id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-surface-500">Username</dt>
                <dd>{intel.user.current_username ? `@${intel.user.current_username}` : "-"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-surface-500">Name</dt>
                <dd>
                  {[intel.user.current_first_name, intel.user.current_last_name]
                    .filter(Boolean)
                    .join(" ") || "-"}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-surface-500">Risk</dt>
                <dd className="badge badge-high">{intel.user.risk_score}</dd>
              </div>
            </dl>
          </div>

          <Panel title="Group profiles" items={intel.profiles || []} />
          <Panel title="Observed aliases" items={intel.aliases || []} />
          <Panel title="Risk signals" items={intel.risk_signals || []} />
          <Panel title="Recent observed messages" items={intel.messages || []} wide />
        </div>
      )}
    </div>
  );
}

function Panel({
  title,
  items,
  wide = false,
}: {
  title: string;
  items: Array<Record<string, unknown>>;
  wide?: boolean;
}) {
  return (
    <div className={wide ? "card xl:col-span-2" : "card"}>
      <h3 className="card-title mb-4">{title}</h3>
      <div className="space-y-3">
        {items.map((item, index) => (
          <pre
            key={index}
            className="max-h-48 overflow-auto rounded-lg bg-surface-900 p-3 text-xs text-white"
          >
            {JSON.stringify(item, null, 2)}
          </pre>
        ))}
        {items.length === 0 && <p className="text-sm text-surface-500">No data yet.</p>}
      </div>
    </div>
  );
}
