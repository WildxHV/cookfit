import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

function NavLink({ to, label }: { to: string; label: string }) {
  const { pathname } = useLocation();
  const active = pathname === to || pathname.startsWith(to + "/");
  return (
    <Link
      to={to}
      className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
        active
          ? "bg-accent-600 text-white"
          : "text-muted hover:bg-accent-50 hover:text-accent-700"
      }`}
    >
      {label}
    </Link>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-gray-100 bg-surface/80 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-5 py-3">
          <Link to="/" className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-xl bg-accent-600 text-lg">
              🥗
            </span>
            <span className="text-lg font-semibold tracking-tight">
              Cook<span className="text-accent-600">Fit</span>
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink to="/ingredient" label="Ingredient" />
            <NavLink to="/recipe" label="Recipe" />
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-5 py-8">{children}</main>
    </div>
  );
}
