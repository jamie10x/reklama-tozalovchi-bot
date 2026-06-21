import { useAuth } from "../../stores/auth";

export function Header() {
  const { logout, officer } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-surface-200 bg-white px-6">
      <div>
        <h1 className="text-lg font-semibold text-surface-900">SecAdmin Panel</h1>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-surface-500">
          {officer?.display_name || officer?.role || "Officer"}
        </span>
        <button onClick={logout} className="btn-ghost text-sm">
          Chiqish
        </button>
      </div>
    </header>
  );
}
