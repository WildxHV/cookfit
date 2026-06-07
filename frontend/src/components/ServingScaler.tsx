import { useI18n } from "../lib/i18n";

interface ServingScalerProps {
  servings: number;
  onChange: (n: number) => void;
}

export function ServingScaler({ servings, onChange }: ServingScalerProps) {
  const { t } = useI18n();
  const set = (n: number) => onChange(Math.min(100, Math.max(1, n)));
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm font-medium text-muted">{t("recipe.people")}</span>
      <div className="flex items-stretch rounded-xl border border-accent-200 bg-accent-50">
        <button
          type="button"
          onClick={() => set(servings - 1)}
          className="px-3 text-lg font-medium text-accent-700 hover:text-accent-900"
          aria-label="Fewer people"
        >
          −
        </button>
        <input
          type="number"
          min={1}
          max={100}
          value={servings}
          onChange={(e) => set(Number(e.target.value) || 1)}
          className="w-14 border-x border-accent-200 bg-transparent text-center text-base font-semibold text-accent-800 outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
        />
        <button
          type="button"
          onClick={() => set(servings + 1)}
          className="px-3 text-lg font-medium text-accent-700 hover:text-accent-900"
          aria-label="More people"
        >
          +
        </button>
      </div>
    </div>
  );
}
