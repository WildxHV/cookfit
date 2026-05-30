import { Link } from "react-router-dom";

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
      className="group flex flex-col gap-3 rounded-3xl border border-gray-100 bg-surface p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-accent-200 hover:shadow-md"
    >
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-accent-50 text-2xl">
        {emoji}
      </span>
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="text-sm leading-relaxed text-muted">{desc}</p>
      <span className="mt-1 text-sm font-medium text-accent-600 group-hover:underline">
        Open →
      </span>
    </Link>
  );
}

export function Home() {
  return (
    <div className="flex flex-col gap-10">
      <section className="pt-6 text-center">
        <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Eat well, the <span className="text-accent-600">Indian</span> way.
        </h1>
        <p className="mx-auto mt-3 max-w-md text-muted">
          Look up the nutrition of any ingredient, or scale a full recipe to any
          number of people — calories, protein, fiber and more, instantly.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2">
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
      </section>
    </div>
  );
}
