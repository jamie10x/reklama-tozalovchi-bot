import { useHealth } from "../api/queries";
import { useI18n } from "../i18n";

export function HealthPage() {
  const { t } = useI18n();
  const { data, isLoading } = useHealth();

  const statusColor = (status: string) => {
    if (status === "healthy") return "bg-severity-low text-white";
    if (status === "degraded") return "bg-severity-medium text-white";
    return "bg-severity-critical text-white";
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">{t("health_title")}</h2>
        <p className="mt-1 text-sm text-surface-500">{t("health_desc")}</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="card">
          <p className="stat-label">{t("api_status")}</p>
          <div className="mt-2 flex items-center gap-3">
            {isLoading ? (
              <div className="h-6 w-20 animate-pulse rounded bg-surface-200" />
            ) : (
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${statusColor(data?.status || "unknown")}`}
              >
                {data?.status || "unknown"}
              </span>
            )}
          </div>
        </div>

        <div className="card">
          <p className="stat-label">{t("database")}</p>
          <div className="mt-2 flex items-center gap-3">
            {isLoading ? (
              <div className="h-6 w-20 animate-pulse rounded bg-surface-200" />
            ) : (
              <span
                className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${statusColor(data?.database || "unknown")}`}
              >
                {data?.database || "unknown"}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
