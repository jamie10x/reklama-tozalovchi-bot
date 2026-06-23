import { apiFetch } from "../api/client";
import { useI18n } from "../i18n";

export function ReportsPage() {
  const { t } = useI18n();
  const handleDownload = async () => {
    try {
      const csv = await apiFetch<string>("/api/v1/reports/events");
      const blob = new Blob([csv], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "security_events.csv";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // handled by apiFetch redirect on 401
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("reports")}</h2>
        <p className="mt-1 text-sm text-surface-500">{t("reports_desc")}</p>
      </div>

      <div className="card">
        <h3 className="card-title mb-2">{t("security_events")}</h3>
        <p className="mb-4 text-sm text-surface-500">
          {t("download_events_csv_desc")}
        </p>
        <button onClick={handleDownload} className="btn-primary">
          {t("download_csv")}
        </button>
      </div>

      <div className="card mt-4">
        <h3 className="card-title mb-2">{t("recurring_reports")}</h3>
        <p className="text-sm text-surface-500">
          {t("recurring_reports_desc")}
        </p>
      </div>
    </div>
  );
}
