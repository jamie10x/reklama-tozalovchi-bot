import { useDashboard } from "../api/queries";

const statCards = [
  { key: "open_events", label: "Ochiq voqealar", color: "text-severity-critical" },
  { key: "critical_events", label: "Muhim voqealar", color: "text-severity-high" },
  { key: "pending_observations", label: "Kutilayotgan kuzatuvlar", color: "text-severity-medium" },
  { key: "total_indicators", label: "Indikatorlar", color: "text-accent-600" },
  { key: "active_groups", label: "Faol guruhlar", color: "text-severity-low" },
  { key: "active_officers", label: "Faol officerlar", color: "text-surface-600" },
];

export function DashboardPage() {
  const { data, isLoading } = useDashboard();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-surface-900">Dashboard</h2>
        <p className="mt-1 text-sm text-surface-500">Tizim holati haqida umumiy ma'lumot</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {statCards.map((card) => (
          <div key={card.key} className="card">
            <p className="stat-label">{card.label}</p>
            <p className={`stat-value ${card.color}`}>
              {isLoading ? (
                <span className="inline-block h-8 w-16 animate-pulse rounded bg-surface-200" />
              ) : (
                data?.[card.key as keyof typeof data] ?? 0
              )}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">So'nggi faollik</h3>
          </div>
          <p className="text-sm text-surface-500">
            Kuzatuv va hodisalar haqida batafsil ma'lumot olish uchun "Voqealar" bo'limiga o'ting.
          </p>
        </div>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Tizim holati</h3>
          </div>
          <p className="text-sm text-surface-500">
            Guruhlar va officerlarning faolligini kuzatish uchun tegishli bo'limlarga o'ting.
          </p>
        </div>
      </div>
    </div>
  );
}
