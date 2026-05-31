import { useEffect, useState } from "react";

// Personalization is stored in the browser (no accounts). `avoid` = allergens /
// things the user doesn't eat; applied to suggestions and recipe warnings.
const KEY = "cookfit:avoid";
const EVENT = "cookfit:prefs";

function read(): string[] {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || "[]");
    return Array.isArray(v) ? v.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}

/** Reactive access to the user's avoid-list, persisted to localStorage and
 *  kept in sync across mounted components (same tab) and other tabs. */
export function usePreferences() {
  const [avoid, setAvoid] = useState<string[]>(read);

  useEffect(() => {
    const handler = () => setAvoid(read());
    window.addEventListener(EVENT, handler);
    window.addEventListener("storage", handler);
    return () => {
      window.removeEventListener(EVENT, handler);
      window.removeEventListener("storage", handler);
    };
  }, []);

  function save(next: string[]) {
    localStorage.setItem(KEY, JSON.stringify(next));
    setAvoid(next);
    window.dispatchEvent(new Event(EVENT));
  }

  function addAvoid(term: string) {
    const t = term.trim();
    if (!t || avoid.some((x) => x.toLowerCase() === t.toLowerCase())) return;
    save([...avoid, t]);
  }

  function removeAvoid(term: string) {
    save(avoid.filter((x) => x !== term));
  }

  return { avoid, addAvoid, removeAvoid };
}

/** True if `text` (an ingredient/dish name) contains an avoided term. */
export function isAvoided(text: string, avoid: string[]): boolean {
  const low = text.toLowerCase();
  return avoid.some((a) => {
    const al = a.toLowerCase().trim();
    return al.length > 0 && (low.includes(al) || al.includes(low));
  });
}
