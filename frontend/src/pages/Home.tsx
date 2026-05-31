import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function ModeCard({
  to,
  emoji,
  title,
  desc,
}: {
  to: string;
  emoji: string;
  title: string;
  desc: string;
}) {
  return (
    <Link
      to={to}
      className="group flex flex-col gap-3 rounded-3xl border border-black/5 bg-surface/80 p-6 shadow-sm backdrop-blur transition hover:-translate-y-1 hover:border-accent-200 hover:shadow-lg hover:shadow-accent-700/5"
    >
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-accent-50 to-accent-100 text-2xl ring-1 ring-inset ring-accent-200/60">
        {emoji}
      </span>
      <h3 className="font-display text-lg font-bold">{title}</h3>
      <p className="text-sm leading-relaxed text-muted">{desc}</p>
      <span className="mt-1 inline-flex items-center gap-1 text-sm font-semibold text-accent-600">
        Open
        <span className="transition-transform group-hover:translate-x-1">→</span>
      </span>
    </Link>
  );
}

export function Home() {
  const [text, setText] = useState("");
  const navigate = useNavigate();

  function go() {
    const have = text
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .join(",");
    navigate(have ? `/cook?have=${encodeURIComponent(have)}` : "/cook");
  }

  return (
    <div className="flex flex-col gap-10">
      {/* Hero — the "what can I make?" cook flow. */}
      <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-accent-700 via-accent-600 to-accent-500 p-7 text-white shadow-xl shadow-accent-800/20 sm:p-10">
        <div
          aria-hidden
          className="pointer-events-none absolute -right-16 -top-20 h-64 w-64 rounded-full bg-white/10 blur-2xl"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -bottom-24 -left-10 h-64 w-64 rounded-full bg-spice-400/20 blur-3xl"
        />
        <div className="relative">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white/90 ring-1 ring-inset ring-white/20">
            ✨ Cook with what you have
          </span>
          <h1 className="font-display mt-4 text-3xl font-extrabold leading-tight sm:text-[2.7rem]">
            What can I cook today?
          </h1>
          <p className="mt-3 max-w-xl text-[15px] leading-relaxed text-white/85">
            Tell us what's in your kitchen and we'll suggest dishes — classic and
            fusion — you can actually make right now, plus matching recipes from
            our catalog.
          </p>

          <div className="mt-6 flex flex-col gap-2.5 sm:flex-row">
            <input
              value={text}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && go()}
              placeholder="paneer, spinach, rice…"
              className="w-full rounded-2xl border-0 bg-white px-5 py-3.5 text-base text-ink shadow-lg shadow-accent-900/10 outline-none ring-2 ring-transparent transition placeholder:text-gray-400 focus:ring-white/70"
            />
            <button
              type="button"
              onClick={go}
              className="shrink-0 rounded-2xl bg-spice-500 px-6 py-3.5 text-base font-semibold text-white shadow-lg shadow-spice-600/30 transition hover:bg-spice-600 active:scale-[0.98]"
            >
              Find dishes →
            </button>
          </div>
          <p className="mt-3 text-xs text-white/70">
            Tip: we assume everyday staples — salt, oil, cumin, ginger, garlic.
          </p>
        </div>
      </section>

      {/* The other two tools. */}
      <section className="flex flex-col gap-4">
        <h2 className="font-display text-sm font-bold uppercase tracking-wide text-muted">
          Or look something up
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <ModeCard
            to="/ingredient"
            emoji="🥣"
            title="Ingredient lookup"
            desc="Pick one item — paneer, moong dal, a roti — set the quantity, toggle raw or cooked, and see the macros recalculate live."
          />
          <ModeCard
            to="/recipe"
            emoji="🍲"
            title="Recipe & servings"
            desc="Search a dish, set the number of people, and get scaled ingredient quantities with per-person and total nutrition."
          />
        </div>
      </section>
    </div>
  );
}
