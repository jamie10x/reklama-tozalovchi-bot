import { useState } from "react";
import { useCases } from "../api/queries";

const severityBadge: Record<string, string> = {
  critical: "badge-critical",
  high: "badge-high",
  medium: "badge-medium",
  low: "badge-low",
};

const statusBadge: Record<string, string> = {
  open: "badge-critical",
  in_progress: "badge-high",
  resolved: "badge-low",
  closed: "badge-info",
};

export function CasesPage() {
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");

  const { data, isLoading } = useCases({
    status: status || undefined,
    severity: severity || undefined,
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Ishlar</h2>
        <p className="mt-1 text-sm text-surface-500">Tergov ishlari</p>
      </div>

      <div className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="input">
              <option value="">Barchasi</option>
              <option value="open">Ochiq</option>
              <option value="in_progress">Jarayonda</option>
              <option value="resolved">Hal qilingan</option>
              <option value="closed">Yopilgan</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">Daraja</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="input">
              <option value="">Barchasi</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
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
                  <th className="pb-3 font-medium">#</th>
                  <th className="pb-3 font-medium">Sarlavha</th>
                  <th className="pb-3 font-medium">Daraja</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">Yaratilgan</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((c) => (
                  <tr key={c.id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 font-mono text-xs">{c.case_number}</td>
                    <td className="py-3 font-medium">{c.title}</td>
                    <td className="py-3">
                      <span className={`badge ${severityBadge[c.severity] || "badge-info"}`}>
                        {c.severity}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`badge ${statusBadge[c.status] || "badge-info"}`}>
                        {c.status}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-surface-500">
                      {new Date(c.created_at).toLocaleString("uz-UZ")}
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
