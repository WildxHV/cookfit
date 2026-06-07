import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { LANGS, useI18n } from "../lib/i18n";

function NavLink({ to, label }: { to: string; label: string }) {
  const { pathname } = useLocation();
  const active = pathname === to || pathname.startsWith(to + "/");
  return (
    <Link
      to={to}
      className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition ${
        active
          ? "bg-gradient-to-br from-accent-500 to-accent-700 text-white shadow-sm shadow-accent-600/30"
          : "text-muted hover:bg-accent-50 hover:text-accent-700"
      }`}
    >
      {label}
    </Link>
  );
}

function LanguageSwitcher() {
  const { lang, setLang } = useI18n();
  return (
    <select
      value={lang}
      onChange={(e) => setLang(e.target.value as typeof lang)}
      aria-label="Language"
      className="rounded-full border border-gray-200 bg-surface px-2.5 py-1.5 text-sm font-medium text-ink outline-none transition hover:border-accent-300 focus:border-accent-400"
    >
      {LANGS.map((l) => (
        <option key={l.code} value={l.code}>
          {l.label}
        </option>
      ))}
    </select>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-20 border-b border-black/5 bg-canvas/70 backdrop-blur-xl">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-2 px-5 py-3">
          <Link to="/" className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-2xl bg-gradient-to-br from-accent-400 to-accent-700 text-lg shadow-sm shadow-accent-700/30">
              🥗
            </span>
            <span className="font-display text-lg font-bold tracking-tight">
              Cook<span className="text-accent-600">Fit</span>
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink to="/ingredient" label={t("nav.ingredient")} />
            <NavLink to="/recipe" label={t("nav.recipe")} />
            <NavLink to="/cook" label={t("nav.cook")} />
            <NavLink to="/preferences" label="⚙" />
            <LanguageSwitcher />
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-5 py-8 sm:py-10">{children}</main>
    </div>
  );
}
