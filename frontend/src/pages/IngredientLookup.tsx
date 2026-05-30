import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  aiLookupIngredient,
  getIngredient,
  searchIngredients,
} from "../api/client";
import type { IngredientSummary } from "../api/types";
import { SearchBox } from "../components/SearchBox";
import { ErrorBanner } from "../components/ErrorBanner";
import { AiBadge } from "../components/AiBadge";
import { NutritionCards } from "../components/NutritionCards";
import { QuantityControl } from "../components/QuantityControl";
import { Segmented } from "../components/Segmented";
import {
  gramsForQuantity,
  macrosForGrams,
  roundMacros,
  unitOptions,
} from "../lib/nutrition";

export function IngredientLookup() {
  const [slug, setSlug] = useState<string | null>(null);
  // Slug that was just fetched via the lookup fallback — drives a one-time
  // "new" badge. Cleared on any normal pick, so repeat searches show no badge.
  const [aiSlug, setAiSlug] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [unit, setUnit] = useState<string>("");
  const [form, setForm] = useState<string>("");

  const { data: detail, isLoading, isError } = useQuery({
    queryKey: ["ingredient", slug],
    queryFn: () => getIngredient(slug!),
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
        onSelect={(i) => {
          setAiSlug(null);
          setSlug(i.slug);
        }}
        aiSearch={aiLookupIngredient}
        onAiResult={(s) => {
          setAiSlug(s);
          setSlug(s);
        }}
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
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-semibold">{detail.name}</h2>
                {aiSlug === detail.slug && <AiBadge />}
              </div>
              <p className="text-xs text-muted capitalize">{detail.category}</p>
            </div>
            {detail.forms.length > 1 && (
              <Segmented options={detail.forms} value={form} onChange={setForm} />
            )}
          </div>

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
        </section>
      )}
    </div>
  );
}
