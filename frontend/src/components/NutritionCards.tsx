import type { Macros } from "../api/types";
import { useI18n } from "../lib/i18n";

const ITEMS: {
  key: keyof Macros;
  labelKey:
    | "macro.calories"
    | "macro.protein"
    | "macro.fiber"
    | "macro.carbs"
    | "macro.fat";
  unit: string;
  accent?: boolean;
}[] = [
  { key: "calories", labelKey: "macro.calories", unit: "kcal", accent: true },
  { key: "protein_g", labelKey: "macro.protein", unit: "g" },
  { key: "fiber_g", labelKey: "macro.fiber", unit: "g" },
  { key: "carbs_g", labelKey: "macro.carbs", unit: "g" },
  { key: "fat_g", labelKey: "macro.fat", unit: "g" },
];

export function NutritionCards({ macros }: { macros: Macros }) {
  const { t } = useI18n();
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
            {t(it.labelKey)}
            <span className="ml-1 text-gray-400">{it.unit}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
