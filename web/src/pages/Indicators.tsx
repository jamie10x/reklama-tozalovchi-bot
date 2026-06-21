import { useState } from "react";
import { useIndicators } from "../api/queries";

const indicatorTypes = [
  { value: "", label: "Barchasi" },
  { value: "domain", label: "Domain" },
  { value: "url", label: "URL" },
  { value: "telegram_username", label: "Telegram username" },
  { value: "email", label: "Email" },
  { value: "phone", label: "Telefon" },
  { value: "wallet", label: "Kripto hamyon" },
  { value: "ip", label: "IP" },
];

const statusBadge: Record<string, string> = {
  suspected: "badge-high",
  confirmed: "badge-critical",
  blocked: "badge-info",
  allowed: "badge-low",
  false_positive: "badge-medium",
  expired: "badge-info",
};

export function IndicatorsPage() {
  const [type, setType] = useState("");
  const [status, setStatus] = useState("");

  const { data, isLoading } = useIndicators({
    limit: 100,
    indicator_type: type || undefined,
    status: status || undefined,
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Indikatorlar</h2>
        <p className="mt-1 text-sm text-surface-500">Xavfsizlik ko'rsatkichlari bazasi</p>
      </div>

      <div className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Tur</label>
            <select value={type} onChange={(e) => setType(e.target.value)} className="input">
              {indicatorTypes.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="input">
              <option value="">Barchasi</option>
              <option value="suspected">Shubhali</option>
              <option value="confirmed">Tasdiqlangan</option>
              <option value="blocked">Bloklangan</option>
              <option value="allowed">Ruxsat etilgan</option>
              <option value="false_positive">Noto'g'ri</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="pb-3 font-medium">Tur</th>
                  <th className="pb-3 font-medium">Qiymat</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Ko'rilgan</th>
                  <th className="pb-3 font-medium">Voqealar</th>
                  <th className="pb-3 font-medium">So'ngi ko'rilgan</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((indicator) => (
                  <tr key={indicator.id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 capitalize">{indicator.indicator_type}</td>
                    <td className="py-3 font-mono text-xs max-w-[200px] truncate">
                      {indicator.indicator_value}
                    </td>
                    <td className="py-3">
                      <span className={`badge ${statusBadge[indicator.status] || "badge-info"}`}>
                        {indicator.status}
                      </span>
                    </td>
                    <td className="py-3">{indicator.seen_count}</td>
                    <td className="py-3">{indicator.event_count}</td>
                    <td className="py-3 text-xs text-surface-500">
                      {indicator.last_seen_at
                        ? new Date(indicator.last_seen_at).toLocaleString("uz-UZ")
                        : "—"}
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
