// Mirrors the backend Pydantic schemas.

export interface Macros {
  calories: number;
  protein_g: number;
  fiber_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface Unit {
  label: string;
  grams: number;
}

export interface IngredientSummary {
  id: number;
  slug: string;
  name: string;
  category: string;
  aliases: string[];
}

export interface SelectedNutrition {
  quantity: number;
  unit: string;
  form: string;
  grams: number;
  nutrition: Macros;
}

export interface IngredientDetail {
  id: number;
  slug: string;
  name: string;
  category: string;
  aliases: string[];
  default_unit: string;
  default_form: string;
  forms: string[];
  units: Unit[];
  facts_per_100g: Record<string, Macros>;
  selected: SelectedNutrition;
}

export interface RecipeSummary {
  id: number;
  slug: string;
  name: string;
  meal_type: string;
  prep_time_min: number | null;
  tags: string[];
  aliases: string[];
}

export interface ScaledIngredient {
  ingredient_id: number;
  slug: string;
  name: string;
  quantity: number;
  unit_label: string;
  form: string;
  grams: number;
  note: string | null;
  nutrition: Macros;
}

export interface RecipeDetail {
  id: number;
  slug: string;
  name: string;
  meal_type: string;
  prep_time_min: number | null;
  instructions: string | null;
  tags: string[];
  aliases: string[];
  servings: number;
  items: ScaledIngredient[];
  per_person: Macros;
  total: Macros;
}
