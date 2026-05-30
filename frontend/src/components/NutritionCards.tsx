import type { Macros } from "../api/types";

const ITEMS: {
  key: keyof Macros;
  label: string;
  unit: string;
  accent?: boolean;
}[] = [
  { key: "calories", label: "Calories", unit: "kcal", accent: true },
  { key: "protein_g", label: "Protein", unit: "g" },
  { key: "fiber_g", label: "Fiber", unit: "g" },
  { key: "carbs_g", label: "Carbs", unit: "g" },
  { key: "fat_g", label: "Fat", unit: "g" },
];

export function NutritionCards({ macros }: { macros: Macros }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {ITEMS.map((it) => (
        <div
          key={it.key}
          className={`rounded-2xl border p-4 text-center ${
            it.accent
              ? "border-accent-200 bg-accent-50"
              : "border-gray-100 bg-surface"
          }`}
        >
          <div
            className={`text-2xl font-semibold tabular-nums ${
              it.accent ? "text-accent-700" : "text-ink"
            }`}
          >
            {macros[it.key]}
          </div>
          <div className="mt-0.5 text-xs font-medium text-muted">
            {it.label}
            <span className="ml-1 text-gray-400">{it.unit}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
