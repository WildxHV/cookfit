import { SIZE_FACTORS, unitIcon, type SizeKey } from "../lib/units";
import { useI18n } from "../lib/i18n";
import { KatoriIcon } from "./KatoriIcon";
import { GlassIcon } from "./GlassIcon";

interface Props {
  unit: string;
  /** Grams of ONE unit at medium size (the catalog value). */
  baseGrams: number;
  value: SizeKey;
  onChange: (size: SizeKey) => void;
}

// Visual scale for the icon so Small/Medium/Large read at a glance.
const ICON_SCALE: Record<SizeKey, string> = {
  S: "text-base",
  M: "text-xl",
  L: "text-2xl",
};
// Matching sizes for the SVG icons.
const KATORI_SCALE: Record<SizeKey, string> = { S: "w-7", M: "w-9", L: "w-12" };
const GLASS_SCALE: Record<SizeKey, string> = { S: "h-7", M: "h-9", L: "h-11" };

export function UnitSizePicker({ unit, baseGrams, value, onChange }: Props) {
  const { t } = useI18n();
  const icon = unitIcon(unit);
  const u = unit.trim().toLowerCase();
  const isKatori = u === "katori" || u === "bowl";
  const isGlass = u === "glass" || u === "mug";
  const sizes: SizeKey[] = ["S", "M", "L"];

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-medium text-muted">
        {t("ing.whichSize", { unit })}
      </p>
      <div className="flex gap-2">
        {sizes.map((s) => {
          const active = s === value;
          const grams = Math.round(baseGrams * SIZE_FACTORS[s]);
          return (
            <button
              key={s}
              type="button"
              onClick={() => onChange(s)}
              aria-pressed={active}
              className={`flex flex-1 flex-col items-center gap-0.5 rounded-2xl border px-3 py-2.5 transition ${
                active
                  ? "border-accent-400 bg-accent-50 ring-2 ring-accent-100"
                  : "border-gray-200 bg-surface hover:border-accent-200"
              }`}
            >
              {isKatori ? (
                <KatoriIcon className={`h-auto ${KATORI_SCALE[s]} drop-shadow-sm`} />
              ) : isGlass ? (
                <GlassIcon className={`w-auto ${GLASS_SCALE[s]} drop-shadow-sm`} />
              ) : (
                <span className={`leading-none ${ICON_SCALE[s]}`} aria-hidden>
                  {icon || "•"}
                </span>
              )}
              <span className="text-xs font-semibold text-ink">
                {t(`size.${s}` as "size.S" | "size.M" | "size.L")}
              </span>
              <span className="text-[11px] tabular-nums text-muted">
                {grams} g
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
