import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { IngredientLookup } from "./pages/IngredientLookup";
import { IngredientRecipes } from "./pages/IngredientRecipes";
import { RecipeView } from "./pages/RecipeView";
import { CookPage } from "./pages/CookPage";
import { Preferences } from "./pages/Preferences";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/ingredient" element={<IngredientLookup />} />
        <Route path="/ingredient/:slug/recipes" element={<IngredientRecipes />} />
        <Route path="/ingredient/:slug" element={<IngredientLookup />} />
        <Route path="/recipe" element={<RecipeView />} />
        <Route path="/recipe/:slug" element={<RecipeView />} />
        <Route path="/cook" element={<CookPage />} />
        <Route path="/preferences" element={<Preferences />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
