import axios from "axios";
import type {
  IngredientDetail,
  IngredientSummary,
  RecipeDetail,
  RecipeSummary,
} from "./types";

// Vite proxies /api -> http://localhost:8000 in dev (see vite.config.ts).
const api = axios.create({ baseURL: "/api/v1" });

export async function searchIngredients(
  q: string,
): Promise<IngredientSummary[]> {
  const { data } = await api.get<IngredientSummary[]>("/ingredients/search", {
    params: { q },
  });
  return data;
}

export async function getIngredient(
  idOrSlug: string,
  params: { quantity?: number; unit?: string; form?: string } = {},
): Promise<IngredientDetail> {
  const { data } = await api.get<IngredientDetail>(
    `/ingredients/${idOrSlug}`,
    { params },
  );
  return data;
}

export async function searchRecipes(q: string): Promise<RecipeSummary[]> {
  const { data } = await api.get<RecipeSummary[]>("/recipes/search", {
    params: { q },
  });
  return data;
}

export async function getRecipe(
  idOrSlug: string,
  servings: number,
): Promise<RecipeDetail> {
  const { data } = await api.get<RecipeDetail>(`/recipes/${idOrSlug}`, {
    params: { servings },
  });
  return data;
}
