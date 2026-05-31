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

// AI fallback: ask the backend to fetch + store a food we don't have yet.
export async function aiLookupIngredient(
  q: string,
): Promise<IngredientDetail> {
  const { data } = await api.get<IngredientDetail>("/ingredients/ai", {
    params: { q },
  });
  return data;
}

export async function getRecipesForIngredient(
  idOrSlug: string,
): Promise<RecipeSummary[]> {
  const { data } = await api.get<RecipeSummary[]>(
    `/ingredients/${idOrSlug}/recipes`,
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

export async function aiLookupRecipe(q: string): Promise<RecipeDetail> {
  const { data } = await api.get<RecipeDetail>("/recipes/ai", {
    params: { q },
  });
  return data;
}
