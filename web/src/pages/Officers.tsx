import { useOfficers } from "../api/queries";

export function OfficersPage() {
  const { data, isLoading } = useOfficers();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Officerlar</h2>
        <p className="mt-1 text-sm text-surface-500">Tizim xodimlari</p>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-surface-100" />
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-surface-200 text-surface-500">
                  <th className="pb-3 font-medium">Telegram ID</th>
                  <th className="pb-3 font-medium">Ism</th>
                  <th className="pb-3 font-medium">Rol</th>
                  <th className="pb-3 font-medium">Holati</th>
                  <th className="pb-3 font-medium">So'ngi kirish</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((o) => (
                  <tr key={o.id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 font-mono text-xs">{o.telegram_id}</td>
                    <td className="py-3 font-medium">{o.display_name || "—"}</td>
                    <td className="py-3 capitalize">{o.role}</td>
                    <td className="py-3">
                      <span className={`badge ${o.is_active ? "badge-low" : "badge-info"}`}>
                        {o.is_active ? "Faol" : "Faol emas"}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-surface-500">
                      {o.last_login_at
                        ? new Date(o.last_login_at).toLocaleString("uz-UZ")
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
