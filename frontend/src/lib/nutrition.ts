import type { Macros, Unit } from "../api/types";

// Mirrors backend app/services/nutrition.py so the lookup screen can
// recalculate live without a server round-trip on every change.

const IMPLICIT_UNIT_GRAMS: Record<string, number> = {
  g: 1,
  gram: 1,
  grams: 1,
  "100g": 100,
  kg: 1000,
};

export function gramsForQuantity(
  quantity: number,
  unitLabel: string,
  units: Unit[],
): number | null {
  const label = unitLabel.trim().toLowerCase();
  if (label in IMPLICIT_UNIT_GRAMS) return quantity * IMPLICIT_UNIT_GRAMS[label];
  const match = units.find((u) => u.label.toLowerCase() === label);
  return match ? quantity * match.grams : null;
}

export function macrosForGrams(per100g: Macros, grams: number): Macros {
  const f = grams / 100;
  return {
    calories: per100g.calories * f,
    protein_g: per100g.protein_g * f,
    fiber_g: per100g.fiber_g * f,
    carbs_g: per100g.carbs_g * f,
    fat_g: per100g.fat_g * f,
  };
}

export function roundMacros(m: Macros): Macros {
  return {
    calories: Math.round(m.calories),
    protein_g: Math.round(m.protein_g * 10) / 10,
    fiber_g: Math.round(m.fiber_g * 10) / 10,
    carbs_g: Math.round(m.carbs_g * 10) / 10,
    fat_g: Math.round(m.fat_g * 10) / 10,
  };
}

// All selectable unit labels for an ingredient: its household units + grams.
export function unitOptions(units: Unit[]): string[] {
  return [...units.map((u) => u.label), "g", "100g"];
}
