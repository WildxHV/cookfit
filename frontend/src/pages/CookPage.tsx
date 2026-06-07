import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { suggestDishes } from "../api/client";
import type { DishSuggestion } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { usePreferences } from "../lib/usePreferences";
import { useI18n } from "../lib/i18n";

function Chip({
  label,
  onRemove,
}: {
  label: string;
  onRemove?: () => void;
}) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-accent-50 px-3 py-1 text-sm font-medium text-accent-700">
      {label}
      {onRemove && (
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 text-accent-500 hover:text-accent-800"
          aria-label={`Remove ${label}`}
        >
          ×
        </button>
      )}
    </span>
  );
}

function KindBadge({ kind }: { kind: string }) {
  const { t } = useI18n();
  const fusion = kind === "fusion";
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
        fusion
          ? "bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-200"
          : "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200"
      }`}
    >
      {fusion ? t("cook.kindFusion") : t("cook.kindClassic")}
    </span>
  );
}

function IdeaCard({ idea }: { idea: DishSuggestion }) {
  return (
    <article className="flex flex-col gap-3 rounded-2xl border border-gray-100 bg-surface p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-lg font-semibold">{idea.name}</h3>
        <KindBadge kind={idea.kind} />
      </div>
      {idea.description && (
        <p className="text-sm leading-relaxed text-muted">{idea.description}</p>
      )}
      {idea.uses.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {idea.uses.map((u) => (
            <Chip key={u} label={u} />
          ))}
        </div>
      )}
      {idea.steps.length > 0 && (
        <ol className="flex flex-col gap-2">
          {idea.steps.map((step, i) => (
            <li key={i} className="flex gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-100 text-xs font-semibold text-accent-700">
                {i + 1}
              </span>
              <span className="pt-0.5 text-sm leading-relaxed text-ink">
                {step}
              </span>
            </li>
          ))}
        </ol>
      )}
    </article>
  );
}

export function CookPage() {
  const [items, setItems] = useState<string[]>([]);
  const [text, setText] = useState("");
  const { avoid } = usePreferences();
  const { t } = useI18n();
  const [searchParams] = useSearchParams();

  const mutation = useMutation({
    mutationFn: (ingredients: string[]) => suggestDishes(ingredients, avoid),
  });
  const mutateRef = useRef(mutation.mutate);
  mutateRef.current = mutation.mutate;

  // Prefill + auto-suggest when arriving from the home hero (?have=a,b,c). The
  // mutate is deferred a tick with cleanup so React's dev double-mount cancels
  // the throwaway call and only the live mount fires.
  useEffect(() => {
    const have = searchParams.get("have");
    if (!have) return;
    const initial = have
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!initial.length) return;
    setItems(initial);
    const id = setTimeout(() => mutateRef.current(initial), 0);
    return () => clearTimeout(id);
  }, [searchParams]);

  function addItem(raw: string) {
    const v = raw.trim().replace(/,$/, "").trim();
    if (!v) return;
    if (!items.some((i) => i.toLowerCase() === v.toLowerCase())) {
      setItems([...items, v]);
    }
    setText("");
  }

  function removeItem(v: string) {
    setItems(items.filter((i) => i !== v));
  }

  const result = mutation.data;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">
          {t("cook.title")}
        </h1>
        <p className="mt-1 text-sm text-muted">{t("cook.subtitle")}</p>
      </div>

      <div className="flex flex-col gap-3 rounded-3xl border border-gray-100 bg-surface p-5 shadow-sm">
        <label className="text-sm font-medium text-ink">
          {t("cook.yourIngredients")}
        </label>
        <input
          value={text}
          onChange={(e) => {
            const v = e.target.value;
            if (v.endsWith(",")) addItem(v);
            else setText(v);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addItem(text);
            } else if (e.key === "Backspace" && !text && items.length) {
              removeItem(items[items.length - 1]);
            }
          }}
          placeholder={t("cook.placeholder")}
          className="w-full rounded-2xl border border-gray-200 bg-surface px-4 py-3 text-base outline-none transition focus:border-accent-400 focus:ring-4 focus:ring-accent-100"
        />
        {items.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {items.map((i) => (
              <Chip key={i} label={i} onRemove={() => removeItem(i)} />
            ))}
          </div>
        )}
        <p className="text-xs text-muted">{t("cook.staples")}</p>
        {avoid.length > 0 && (
          <p className="text-xs text-red-600">
            {t("cook.avoiding")} {avoid.join(", ")}.{" "}
            <Link to="/preferences" className="underline">
              {t("cook.edit")}
            </Link>
          </p>
        )}
        <div>
          <button
            type="button"
            disabled={items.length === 0 || mutation.isPending}
            onClick={() => mutation.mutate(items)}
            className="rounded-2xl bg-gradient-to-br from-accent-500 to-accent-700 px-6 py-2.5 text-sm font-semibold text-white shadow-sm shadow-accent-700/30 transition hover:brightness-105 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
          >
            {mutation.isPending ? t("cook.suggesting") : t("cook.suggest")}
          </button>
        </div>
      </div>

      {mutation.isError && <ErrorBanner />}

      {result && (
        <>
          {result.from_catalog.length > 0 && (
            <section className="flex flex-col gap-3">
              <h2 className="text-lg font-semibold">
                {t("cook.fromOurRecipes")}
              </h2>
              <ul className="grid gap-3 sm:grid-cols-2">
                {result.from_catalog.map((m) => (
                  <li key={m.slug}>
                    <Link
                      to={`/recipe/${m.slug}`}
                      className="flex h-full flex-col gap-1.5 rounded-2xl border border-gray-100 bg-surface p-4 shadow-sm transition hover:border-accent-300 hover:shadow"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold">{m.name}</span>
                        <span className="text-xs text-muted capitalize">
                          {m.meal_type}
                        </span>
                      </div>
                      {m.missing.length > 0 ? (
                        <span className="text-xs text-amber-600">
                          {t("cook.justNeed")} {m.missing.join(", ")}
                        </span>
                      ) : (
                        <span className="text-xs text-emerald-600">
                          {t("cook.haveEverything")}
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold">{t("cook.ideasToTry")}</h2>
            {result.ideas.length > 0 ? (
              <div className="grid gap-4">
                {result.ideas.map((idea) => (
                  <IdeaCard key={idea.name} idea={idea} />
                ))}
              </div>
            ) : (
              <p className="rounded-2xl border border-dashed border-gray-200 p-6 text-center text-sm text-muted">
                {result.ai_error ?? t("cook.noIdeas")}
              </p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
