// Visual cues + size handling for household units. A katori/cup/bowl/glass or a
// spoon varies a lot between kitchens, so for those units we let the user pick a
// size (small / medium / large) that scales the grams for a more exact number.

const BOWL_UNITS = ["katori", "cup", "bowl", "glass", "mug"];
const SPOON_UNITS = ["tbsp", "tsp", "spoon", "tablespoon", "teaspoon"];

export type SizeKey = "S" | "M" | "L";

// Medium = the catalog's stated gram weight; small/large scale around it.
export const SIZE_FACTORS: Record<SizeKey, number> = { S: 0.75, M: 1, L: 1.3 };
export const SIZE_LABELS: Record<SizeKey, string> = {
  S: "Small",
  M: "Medium",
  L: "Large",
};

/** An emoji cue for a unit, or "" if it isn't a bowl/spoon-style measure. */
export function unitIcon(label: string): string {
  const l = label.trim().toLowerCase();
  if (l === "glass" || l === "mug") return "🥛";
  if (BOWL_UNITS.includes(l)) return "🥣";
  if (SPOON_UNITS.includes(l)) return "🥄";
  return "";
}

/** Whether this unit's real-world size varies enough to offer a size picker. */
export function isSizable(label: string): boolean {
  const l = label.trim().toLowerCase();
  return BOWL_UNITS.includes(l) || SPOON_UNITS.includes(l);
}
