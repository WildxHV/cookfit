import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getRecipe, searchRecipes } from "../api/client";
import type { RecipeSummary } from "../api/types";
import { SearchBox } from "../components/SearchBox";
import { NutritionCards } from "../components/NutritionCards";
import { ServingScaler } from "../components/ServingScaler";
import { Segmented } from "../components/Segmented";

function Tag({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-accent-50 px-2.5 py-0.5 text-xs font-medium text-accent-700">
      {label.replace(/_/g, " ")}
    </span>
  );
}

export function RecipeView() {
  const [slug, setSlug] = useState<string | null>(null);
  const [servings, setServings] = useState(1);
  const [view, setView] = useState<"per person" | "total">("per person");

  const { data: recipe, isLoading } = useQuery({
    queryKey: ["recipe", slug, servings],
    queryFn: () => getRecipe(slug!, servings),
    enabled: !!slug,
    placeholderData: (prev) => prev, // keep showing old data while refetching
  });

  const macros =
    recipe && (view === "per person" ? recipe.per_person : recipe.total);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Recipe & servings</h1>
        <p className="mt-1 text-sm text-muted">
          Search a dish, set the number of people, and get scaled quantities with
          per-person and total nutrition.
        </p>
      </div>

      <SearchBox<RecipeSummary>
        placeholder="Try “dal tadka”, “rajma”, “palak paneer”…"
        queryKey="recipe-search"
        search={searchRecipes}
        getKey={(r) => r.id}
        renderItem={(r) => (
          <div className="flex items-center justify-between">
            <span className="font-medium">{r.name}</span>
            <span className="text-xs text-muted capitalize">{r.meal_type}</span>
          </div>
        )}
        onSelect={(r) => {
          setSlug(r.slug);
          setServings(1);
        }}
      />

      {!slug && (
        <div className="rounded-3xl border border-dashed border-gray-200 p-10 text-center text-sm text-muted">
          Pick a dish to see its scaled ingredients and nutrition.
        </div>
      )}

      {slug && isLoading && (
        <div className="rounded-3xl border border-gray-100 bg-surface p-6 text-sm text-muted">
          Loading…
        </div>
      )}

      {recipe && macros && (
        <section className="flex flex-col gap-5 rounded-3xl border border-gray-100 bg-surface p-6 shadow-sm">
          <div className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold">{recipe.name}</h2>
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
              <span className="capitalize">{recipe.meal_type}</span>
              {recipe.prep_time_min && <span>· {recipe.prep_time_min} min</span>}
              {recipe.tags.map((t) => (
                <Tag key={t} label={t} />
              ))}
            </div>
          </div>

          {/* Serving scaler pinned at the top of the result. */}
          <div className="sticky top-16 z-10 -mx-6 flex items-center justify-between border-y border-gray-100 bg-surface/95 px-6 py-3 backdrop-blur">
            <ServingScaler servings={servings} onChange={setServings} />
            <Segmented
              options={["per person", "total"]}
              value={view}
              onChange={(v) => setView(v as "per person" | "total")}
            />
          </div>

          <NutritionCards macros={macros} />

          <div>
            <h3 className="mb-2 text-sm font-semibold text-muted">
              Ingredients for {servings} {servings === 1 ? "person" : "people"}
            </h3>
            <ul className="divide-y divide-gray-100 overflow-hidden rounded-2xl border border-gray-100">
              {recipe.items.map((it) => (
                <li
                  key={it.ingredient_id}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <div className="min-w-0">
                    <span className="font-medium">{it.name}</span>
                    {it.note && (
                      <span className="ml-2 text-xs text-muted">{it.note}</span>
                    )}
                  </div>
                  <div className="flex shrink-0 items-center gap-4 text-sm">
                    <span className="tabular-nums text-ink">
                      {it.quantity} {it.unit_label}
                    </span>
                    <span className="w-16 text-right tabular-nums text-muted">
                      {it.nutrition.calories} kcal
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {recipe.instructions && (
            <div>
              <h3 className="mb-1 text-sm font-semibold text-muted">Method</h3>
              <p className="text-sm leading-relaxed text-ink">
                {recipe.instructions}
              </p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
