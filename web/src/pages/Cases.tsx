import { useState } from "react";
import { useCases } from "../api/queries";
import { useI18n } from "../i18n";

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
  const { t } = useI18n();
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");

  const { data, isLoading } = useCases({
    status: status || undefined,
    severity: severity || undefined,
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("cases")}</h2>
        <p className="mt-1 text-sm text-surface-500">{t("cases_desc")}</p>
      </div>

      <div className="card mb-6">
        <div className="flex flex-wrap gap-4">
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("status")}</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)} className="input">
              <option value="">{t("all")}</option>
              <option value="open">{t("open")}</option>
              <option value="in_progress">{t("in_progress")}</option>
              <option value="resolved">{t("resolved")}</option>
              <option value="closed">{t("closed")}</option>
            </select>
          </div>
          <div className="min-w-[160px]">
            <label className="mb-1 block text-xs font-medium text-surface-500">{t("severity")}</label>
            <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="input">
              <option value="">{t("all")}</option>
              <option value="critical">{t("critical")}</option>
              <option value="high">{t("high")}</option>
              <option value="medium">{t("medium")}</option>
              <option value="low">{t("low")}</option>
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
                  <th className="pb-3 font-medium">{t("title")}</th>
                  <th className="pb-3 font-medium">{t("severity")}</th>
                  <th className="pb-3 font-medium">{t("status")}</th>
                  <th className="pb-3 font-medium">{t("created")}</th>
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
