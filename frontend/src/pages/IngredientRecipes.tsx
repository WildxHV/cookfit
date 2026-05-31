import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { getIngredient, getRecipesForIngredient } from "../api/client";
import { ErrorBanner } from "../components/ErrorBanner";

function Tag({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-accent-50 px-2 py-0.5 text-xs font-medium text-accent-700">
      {label.replace(/_/g, " ")}
    </span>
  );
}

export function IngredientRecipes() {
  const { slug } = useParams();

  const { data: ingredient } = useQuery({
    queryKey: ["ingredient", slug],
    queryFn: () => getIngredient(slug!),
    enabled: !!slug,
  });

  const { data: recipes, isLoading, isError } = useQuery({
    queryKey: ["ingredient-recipes", slug],
    queryFn: () => getRecipesForIngredient(slug!),
    enabled: !!slug,
  });

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link
          to={`/ingredient/${slug}`}
          className="text-sm font-medium text-accent-700 hover:underline"
        >
          ← Back to {ingredient?.name ?? "ingredient"}
        </Link>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">
          Recipes with {ingredient?.name ?? "this ingredient"}
        </h1>
        {recipes && (
          <p className="mt-1 text-sm text-muted">
            {recipes.length} {recipes.length === 1 ? "recipe" : "recipes"} in our
            catalog.
          </p>
        )}
      </div>

      {isLoading && (
        <div className="rounded-3xl border border-gray-100 bg-surface p-6 text-sm text-muted">
          Loading…
        </div>
      )}

      {isError && <ErrorBanner />}

      {recipes && recipes.length === 0 && (
        <div className="rounded-3xl border border-dashed border-gray-200 p-10 text-center text-sm text-muted">
          No recipes use this ingredient yet.
        </div>
      )}

      {recipes && recipes.length > 0 && (
        <ul className="grid gap-3 sm:grid-cols-2">
          {recipes.map((r) => (
            <li key={r.id}>
              <Link
                to={`/recipe/${r.slug}`}
                className="flex h-full flex-col gap-2 rounded-2xl border border-gray-100 bg-surface p-4 shadow-sm transition hover:border-accent-300 hover:shadow"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold">{r.name}</span>
                  <span className="text-xs text-muted capitalize">
                    {r.meal_type}
                  </span>
                </div>
                {r.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {r.tags.slice(0, 4).map((t) => (
                      <Tag key={t} label={t} />
                    ))}
                  </div>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
