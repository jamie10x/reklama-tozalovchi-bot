import { useState } from "react";
import { useAuditLogs } from "../api/queries";
import { useI18n } from "../i18n";

export function AuditLogPage() {
  const { t } = useI18n();
  const [actionType, setActionType] = useState("");

  const { data, isLoading } = useAuditLogs({
    limit: 100,
    action_type: actionType || undefined,
  });

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("audit_log")}</h2>
        <p className="mt-1 text-sm text-surface-500">{t("audit_desc")}</p>
      </div>

      <div className="card mb-6">
        <div className="min-w-[200px]">
          <label className="mb-1 block text-xs font-medium text-surface-500">{t("action_type")}</label>
          <select
            value={actionType}
            onChange={(e) => setActionType(e.target.value)}
            className="input"
          >
            <option value="">{t("all")}</option>
            <option value="event_status_update">{t("event_status_update")}</option>
            <option value="indicator_status_update">{t("indicator_status_update")}</option>
            <option value="case_created">{t("case_created")}</option>
            <option value="case_updated">{t("case_updated")}</option>
            <option value="enforcement_requested">{t("enforcement_requested")}</option>
          </select>
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
                  <th className="pb-3 font-medium">{t("action")}</th>
                  <th className="pb-3 font-medium">{t("resource")}</th>
                  <th className="pb-3 font-medium">{t("resource_id")}</th>
                  <th className="pb-3 font-medium">{t("time")}</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((log) => (
                  <tr key={log.id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3">
                      <code className="rounded bg-surface-100 px-2 py-0.5 text-xs">
                        {log.action_type}
                      </code>
                    </td>
                    <td className="py-3 capitalize">{log.resource_type}</td>
                    <td className="py-3 font-mono text-xs">{log.resource_id}</td>
                    <td className="py-3 text-xs text-surface-500">
                      {new Date(log.created_at).toLocaleString("uz-UZ")}
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
