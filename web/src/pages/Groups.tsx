import { useGroups } from "../api/queries";

export function GroupsPage() {
  const { data, isLoading } = useGroups();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Guruhlar</h2>
        <p className="mt-1 text-sm text-surface-500">Himoya qilinayotgan guruhlar</p>
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
                  <th className="pb-3 font-medium">Chat ID</th>
                  <th className="pb-3 font-medium">Nomi</th>
                  <th className="pb-3 font-medium">Holati</th>
                  <th className="pb-3 font-medium">Rejim</th>
                  <th className="pb-3 font-medium">O'chira oladi</th>
                  <th className="pb-3 font-medium">Qo'shilgan</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((group) => (
                  <tr key={group.telegram_chat_id} className="border-b border-surface-100 hover:bg-surface-50">
                    <td className="py-3 font-mono text-xs">{group.telegram_chat_id}</td>
                    <td className="py-3 font-medium">{group.title || "Nomsiz"}</td>
                    <td className="py-3">
                      <span className={`badge ${group.enabled ? "badge-low" : "badge-info"}`}>
                        {group.enabled ? "Faol" : "O'chirilgan"}
                      </span>
                    </td>
                    <td className="py-3 capitalize">{group.mode}</td>
                    <td className="py-3">{group.bot_can_delete_messages ? "✅" : "❌"}</td>
                    <td className="py-3 text-xs text-surface-500">
                      {new Date(group.created_at).toLocaleString("uz-UZ")}
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
