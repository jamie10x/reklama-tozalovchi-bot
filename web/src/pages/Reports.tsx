import { apiFetch } from "../api/client";

export function ReportsPage() {
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
        <h2 className="text-2xl font-bold text-surface-900">Hisobotlar</h2>
        <p className="mt-1 text-sm text-surface-500">Ma'lumotlarni eksport qilish</p>
      </div>

      <div className="card">
        <h3 className="card-title mb-2">Xavfsizlik voqealari</h3>
        <p className="mb-4 text-sm text-surface-500">
          Barcha xavfsizlik voqealarini CSV formatida yuklab oling.
        </p>
        <button onClick={handleDownload} className="btn-primary">
          CSV yuklab olish
        </button>
      </div>

      <div className="card mt-4">
        <h3 className="card-title mb-2">Davriy hisobotlar</h3>
        <p className="text-sm text-surface-500">
          Davriy hisobotlar funksiyasi ishlab chiqilmoqda.
        </p>
      </div>
    </div>
  );
}
