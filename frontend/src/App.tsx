import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Home } from "./pages/Home";
import { IngredientLookup } from "./pages/IngredientLookup";
import { RecipeView } from "./pages/RecipeView";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/ingredient" element={<IngredientLookup />} />
        <Route path="/recipe" element={<RecipeView />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
