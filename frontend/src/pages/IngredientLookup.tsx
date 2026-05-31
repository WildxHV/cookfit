import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  aiLookupIngredient,
  getIngredient,
  getRecipesForIngredient,
  searchIngredients,
} from "../api/client";
import type { IngredientSummary } from "../api/types";
import { SearchBox } from "../components/SearchBox";
import { ErrorBanner } from "../components/ErrorBanner";
import { NutritionCards } from "../components/NutritionCards";
import { QuantityControl } from "../components/QuantityControl";
import { Segmented } from "../components/Segmented";
import {
  gramsForQuantity,
  macrosForGrams,
  roundMacros,
  unitOptions,
} from "../lib/nutrition";
import { usePreferences, isAvoided } from "../lib/usePreferences";

function Chip({ label }: { label: string }) {
  return (
    <span className="rounded-full bg-accent-50 px-2.5 py-0.5 text-xs font-medium text-accent-700">
      {label}
    </span>
  );
}

const TOP_N = 5;

export function IngredientLookup() {
  const { slug: routeSlug } = useParams();
  const navigate = useNavigate();
  const slug = routeSlug ?? null;

  const [quantity, setQuantity] = useState(1);
  const [unit, setUnit] = useState<string>("");
  const [form, setForm] = useState<string>("");
  const { avoid } = usePreferences();

  const { data: detail, isLoading, isError } = useQuery({
    queryKey: ["ingredient", slug],
    queryFn: () => getIngredient(slug!),
    enabled: !!slug,
  });

  const { data: usedIn } = useQuery({
    queryKey: ["ingredient-recipes", slug],
    queryFn: () => getRecipesForIngredient(slug!),
    enabled: !!slug,
  });

  // Initialize controls whenever a new ingredient loads.
  useEffect(() => {
    if (detail) {
      setQuantity(1);
      setUnit(detail.default_unit);
      setForm(detail.default_form);
    }
  }, [detail]);

  const grams =
    detail && unit ? gramsForQuantity(quantity, unit, detail.units) : null;
  const per100g = detail && form ? detail.facts_per_100g[form] : undefined;
  const macros =
    per100g && grams !== null
      ? roundMacros(macrosForGrams(per100g, grams))
      : null;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Ingredient lookup</h1>
        <p className="mt-1 text-sm text-muted">
          Search any ingredient, set the amount, and see the nutrition update
          live.
        </p>
      </div>

      <SearchBox<IngredientSummary>
        placeholder="Try “paneer”, “moong dal”, “chana”…"
        queryKey="ing-search"
        search={searchIngredients}
        getKey={(i) => i.id}
        renderItem={(i) => (
          <div className="flex items-center justify-between">
            <span className="font-medium">{i.name}</span>
            <span className="text-xs text-muted capitalize">{i.category}</span>
          </div>
        )}
        onSelect={(i) => navigate(`/ingredient/${i.slug}`)}
        aiSearch={aiLookupIngredient}
        onAiResult={(s) => navigate(`/ingredient/${s}`)}
        aiNoun="ingredient"
      />

      {!slug && (
        <div className="rounded-3xl border border-dashed border-gray-200 p-10 text-center text-sm text-muted">
          Pick an ingredient to see its calories, protein, fiber, carbs and fat.
        </div>
      )}

      {slug && isLoading && (
        <div className="rounded-3xl border border-gray-100 bg-surface p-6 text-sm text-muted">
          Loading…
        </div>
      )}

      {slug && isError && <ErrorBanner />}

      {detail && macros && (
        <section className="flex flex-col gap-5 rounded-3xl border border-gray-100 bg-surface p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">{detail.name}</h2>
              <p className="text-xs text-muted capitalize">{detail.category}</p>
            </div>
            {detail.forms.length > 1 && (
              <Segmented options={detail.forms} value={form} onChange={setForm} />
            )}
          </div>

          {isAvoided(detail.name, avoid) && (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
              ⚠ You've marked this as something you avoid.
            </div>
          )}

          {detail.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {detail.tags.map((t) => (
                <Chip key={t} label={t} />
              ))}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-4">
            <QuantityControl
              quantity={quantity}
              unit={unit}
              unitOptions={unitOptions(detail.units)}
              onQuantityChange={setQuantity}
              onUnitChange={setUnit}
            />
            {grams !== null && (
              <span className="text-sm text-muted">
                = <span className="font-medium text-ink">{Math.round(grams)} g</span>
              </span>
            )}
          </div>

          <NutritionCards macros={macros} />

          {usedIn && usedIn.length > 0 && (
            <div className="border-t border-gray-100 pt-4">
              <h3 className="mb-2 text-sm font-semibold text-muted">
                Used in recipes
              </h3>
              <ul className="divide-y divide-gray-100 overflow-hidden rounded-2xl border border-gray-100">
                {usedIn.slice(0, TOP_N).map((r) => (
                  <li key={r.id}>
                    <Link
                      to={`/recipe/${r.slug}`}
                      className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-accent-50"
                    >
                      <span className="font-medium">{r.name}</span>
                      <span className="text-xs text-muted capitalize">
                        {r.meal_type}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
              {usedIn.length > TOP_N && (
                <Link
                  to={`/ingredient/${detail.slug}/recipes`}
                  className="mt-2 inline-block text-sm font-medium text-accent-700 hover:underline"
                >
                  View all {usedIn.length} recipes →
                </Link>
              )}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
