import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

// Lightweight, dependency-free i18n for the UI chrome. Dynamic content
// (ingredient/recipe names from the DB) stays as-is; this translates the
// static labels, headings and buttons. Choice is remembered in localStorage.

export type Lang = "en" | "hi";

export const LANGS: { code: Lang; label: string }[] = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
];

type Dict = Record<string, string>;

const en: Dict = {
  "nav.ingredient": "Ingredient",
  "nav.recipe": "Recipe",
  "nav.cook": "Cook",

  "home.heroPill": "Cook with what you have",
  "home.heroTitle": "What can I cook today?",
  "home.heroSubtitle":
    "Tell us what's in your kitchen and we'll suggest dishes — classic and fusion — you can actually make right now, plus matching recipes from our catalog.",
  "home.heroPlaceholder": "paneer, spinach, rice…",
  "home.heroButton": "Find dishes →",
  "home.heroTip":
    "Tip: we assume everyday staples — salt, oil, cumin, ginger, garlic.",
  "home.orLookUp": "Or look something up",
  "home.ingredientTitle": "Ingredient lookup",
  "home.ingredientDesc":
    "Pick one item — paneer, moong dal, a roti — set the quantity, toggle raw or cooked, and see the macros recalculate live.",
  "home.recipeTitle": "Recipe & servings",
  "home.recipeDesc":
    "Search a dish, set the number of people, and get scaled ingredient quantities with per-person and total nutrition.",
  "home.open": "Open",

  "ing.title": "Ingredient lookup",
  "ing.subtitle": "Search any ingredient, set the amount, and see the nutrition update live.",
  "ing.searchPlaceholder": "Try “paneer”, “moong dal”, “chana”…",
  "ing.empty": "Pick an ingredient to see its calories, protein, fiber, carbs and fat.",
  "ing.avoidWarning": "⚠ You've marked this as something you avoid.",
  "ing.howMuch": "How much?",
  "ing.weighedAs": "weighed as",
  "ing.cookedServing1": "A",
  "ing.cookedServing2": "is measured as a",
  "ing.cooked": "cooked",
  "ing.cookedServing3": "serving.",
  "ing.whichSize": "Which size {unit} do you have?",
  "ing.usedIn": "Used in recipes",
  "ing.viewAll": "View all {n} recipes →",

  "size.S": "Small",
  "size.M": "Medium",
  "size.L": "Large",

  "macro.calories": "Calories",
  "macro.protein": "Protein",
  "macro.fiber": "Fiber",
  "macro.carbs": "Carbs",
  "macro.fat": "Fat",

  "recipe.title": "Recipe & servings",
  "recipe.subtitle":
    "Search a dish, set the number of people, and get scaled quantities with per-person and total nutrition.",
  "recipe.searchPlaceholder": "Try “dal tadka”, “rajma”, “palak paneer”…",
  "recipe.empty": "Pick a dish to see its scaled ingredients and nutrition.",
  "recipe.people": "Number of people",
  "recipe.perPerson": "per person",
  "recipe.total": "total",
  "recipe.ingredientsFor": "Ingredients for",
  "recipe.person": "person",
  "recipe.people_plural": "people",
  "recipe.method": "Method",
  "recipe.avoidWarning": "⚠ Heads up — this recipe contains {items}, which you've chosen to avoid.",

  "cook.title": "What can I make?",
  "cook.subtitle":
    "List the ingredients you have and we'll suggest dishes — classic and fusion — you can cook right now.",
  "cook.yourIngredients": "Your ingredients",
  "cook.placeholder": "Type an ingredient and press Enter (e.g. palak, paneer, pasta)…",
  "cook.staples":
    "We'll assume you also have everyday staples — salt, oil, cumin, chili, turmeric, ginger, garlic and onion.",
  "cook.avoiding": "Avoiding:",
  "cook.edit": "Edit",
  "cook.suggest": "Suggest dishes",
  "cook.suggesting": "Cooking up ideas…",
  "cook.fromOurRecipes": "From our recipes",
  "cook.ideasToTry": "Ideas to try",
  "cook.justNeed": "Just need:",
  "cook.haveEverything": "You have everything!",
  "cook.kindFusion": "fusion",
  "cook.kindClassic": "classic",
  "cook.noIdeas": "No ideas just now — try different ingredients.",

  "prefs.title": "Your preferences",
  "prefs.subtitle":
    "List anything you're allergic to or simply don't eat. We'll remember it on this device and keep it out of your suggestions — and flag any recipe that contains it.",
  "prefs.label": "Allergens & things you avoid",
  "prefs.placeholder": "e.g. peanuts, mushroom, gluten — press Enter to add",
  "prefs.empty": "Nothing added yet — suggestions will include everything.",
  "prefs.language": "Language",

  "common.loading": "Loading…",
  "common.error": "Something went wrong. Is the backend running on port 8000?",
  "search.searching": "Searching…",
  "search.lookUp": "Look up",
  "search.lookingUp": "Looking up",
  "search.noMatches": "No matches.",
};

const hi: Dict = {
  "nav.ingredient": "सामग्री",
  "nav.recipe": "रेसिपी",
  "nav.cook": "बनाएँ",

  "home.heroPill": "जो है उसी से पकाएँ",
  "home.heroTitle": "आज क्या बनाऊँ?",
  "home.heroSubtitle":
    "बताइए आपकी रसोई में क्या है और हम ऐसे व्यंजन सुझाएँगे — पारंपरिक और फ्यूज़न — जो आप अभी बना सकते हैं, साथ ही हमारे संग्रह से मिलती-जुलती रेसिपी।",
  "home.heroPlaceholder": "पनीर, पालक, चावल…",
  "home.heroButton": "व्यंजन खोजें →",
  "home.heroTip":
    "सुझाव: हम मानते हैं कि रोज़मर्रा की चीज़ें — नमक, तेल, जीरा, अदरक, लहसुन — आपके पास हैं।",
  "home.orLookUp": "या कुछ खोजें",
  "home.ingredientTitle": "सामग्री खोज",
  "home.ingredientDesc":
    "कोई एक चीज़ चुनें — पनीर, मूंग दाल, रोटी — मात्रा तय करें, कच्चा या पका टॉगल करें, और पोषण को तुरंत बदलते देखें।",
  "home.recipeTitle": "रेसिपी और मात्रा",
  "home.recipeDesc":
    "कोई व्यंजन खोजें, लोगों की संख्या तय करें, और प्रति-व्यक्ति व कुल पोषण के साथ मापी हुई मात्रा पाएँ।",
  "home.open": "खोलें",

  "ing.title": "सामग्री खोज",
  "ing.subtitle": "कोई भी सामग्री खोजें, मात्रा तय करें, और पोषण को तुरंत बदलते देखें।",
  "ing.searchPlaceholder": "“पनीर”, “मूंग दाल”, “चना” आज़माएँ…",
  "ing.empty": "इसकी कैलोरी, प्रोटीन, फाइबर, कार्ब्स और फैट देखने के लिए कोई सामग्री चुनें।",
  "ing.avoidWarning": "⚠ आपने इसे टालने वाली चीज़ों में रखा है।",
  "ing.howMuch": "कितना?",
  "ing.weighedAs": "किस रूप में",
  "ing.cookedServing1": "एक",
  "ing.cookedServing2": "को",
  "ing.cooked": "पकी हुई",
  "ing.cookedServing3": "मात्रा के रूप में मापा जाता है।",
  "ing.whichSize": "आपके पास किस आकार की {unit} है?",
  "ing.usedIn": "इन रेसिपी में",
  "ing.viewAll": "सभी {n} रेसिपी देखें →",

  "size.S": "छोटी",
  "size.M": "मध्यम",
  "size.L": "बड़ी",

  "macro.calories": "कैलोरी",
  "macro.protein": "प्रोटीन",
  "macro.fiber": "फाइबर",
  "macro.carbs": "कार्ब्स",
  "macro.fat": "फैट",

  "recipe.title": "रेसिपी और मात्रा",
  "recipe.subtitle":
    "कोई व्यंजन खोजें, लोगों की संख्या तय करें, और प्रति-व्यक्ति व कुल पोषण के साथ मापी हुई मात्रा पाएँ।",
  "recipe.searchPlaceholder": "“दाल तड़का”, “राजमा”, “पालक पनीर” आज़माएँ…",
  "recipe.empty": "इसकी मापी हुई सामग्री और पोषण देखने के लिए कोई व्यंजन चुनें।",
  "recipe.people": "लोगों की संख्या",
  "recipe.perPerson": "प्रति व्यक्ति",
  "recipe.total": "कुल",
  "recipe.ingredientsFor": "सामग्री —",
  "recipe.person": "व्यक्ति",
  "recipe.people_plural": "लोग",
  "recipe.method": "विधि",
  "recipe.avoidWarning": "⚠ ध्यान दें — इस रेसिपी में {items} है, जिसे आपने टालना चुना है।",

  "cook.title": "मैं क्या बना सकता/सकती हूँ?",
  "cook.subtitle":
    "आपके पास मौजूद सामग्री बताएँ और हम ऐसे व्यंजन सुझाएँगे — पारंपरिक और फ्यूज़न — जो आप अभी बना सकते हैं।",
  "cook.yourIngredients": "आपकी सामग्री",
  "cook.placeholder": "एक सामग्री लिखें और Enter दबाएँ (जैसे पालक, पनीर, पास्ता)…",
  "cook.staples":
    "हम मानेंगे कि रोज़मर्रा की चीज़ें भी आपके पास हैं — नमक, तेल, जीरा, मिर्च, हल्दी, अदरक, लहसुन और प्याज़।",
  "cook.avoiding": "टाल रहे हैं:",
  "cook.edit": "बदलें",
  "cook.suggest": "व्यंजन सुझाएँ",
  "cook.suggesting": "विचार बन रहे हैं…",
  "cook.fromOurRecipes": "हमारी रेसिपी से",
  "cook.ideasToTry": "आज़माने योग्य विचार",
  "cook.justNeed": "बस चाहिए:",
  "cook.haveEverything": "आपके पास सब कुछ है!",
  "cook.kindFusion": "फ्यूज़न",
  "cook.kindClassic": "पारंपरिक",
  "cook.noIdeas": "अभी कोई सुझाव नहीं — कुछ अलग सामग्री आज़माएँ।",

  "prefs.title": "आपकी पसंद",
  "prefs.subtitle":
    "जिनसे आपको एलर्जी है या जो आप नहीं खाते, उन्हें लिखें। हम इसे इस डिवाइस पर याद रखेंगे और आपके सुझावों से बाहर रखेंगे — और जिस रेसिपी में हो उसे चिह्नित करेंगे।",
  "prefs.label": "एलर्जी और टाली जाने वाली चीज़ें",
  "prefs.placeholder": "जैसे मूंगफली, मशरूम, ग्लूटेन — जोड़ने के लिए Enter दबाएँ",
  "prefs.empty": "अभी कुछ नहीं जोड़ा — सुझावों में सब कुछ शामिल होगा।",
  "prefs.language": "भाषा",

  "common.loading": "लोड हो रहा है…",
  "common.error": "कुछ गड़बड़ हुई। क्या बैकएंड पोर्ट 8000 पर चल रहा है?",
  "search.searching": "खोज रहे हैं…",
  "search.lookUp": "खोजें",
  "search.lookingUp": "खोज रहे हैं",
  "search.noMatches": "कोई मिलान नहीं।",
};

const DICTS: Record<Lang, Dict> = { en, hi };

const KEY = "cookfit:lang";

interface I18nCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: keyof typeof en, vars?: Record<string, string | number>) => string;
}

const Ctx = createContext<I18nCtx | null>(null);

function readLang(): Lang {
  const v = localStorage.getItem(KEY);
  return v === "hi" || v === "en" ? v : "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readLang);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18nCtx>(() => {
    const setLang = (l: Lang) => {
      localStorage.setItem(KEY, l);
      setLangState(l);
    };
    const t: I18nCtx["t"] = (key, vars) => {
      let s = DICTS[lang][key] ?? en[key] ?? String(key);
      if (vars) {
        for (const [k, val] of Object.entries(vars)) {
          s = s.replace(new RegExp(`\\{${k}\\}`, "g"), String(val));
        }
      }
      return s;
    };
    return { lang, setLang, t };
  }, [lang]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useI18n(): I18nCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
