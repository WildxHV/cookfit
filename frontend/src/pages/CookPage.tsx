import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { suggestDishes } from "../api/client";
import type { DishSuggestion } from "../api/types";
import { ErrorBanner } from "../components/ErrorBanner";
import { usePreferences } from "../lib/usePreferences";

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
  const fusion = kind === "fusion";
  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
        fusion
          ? "bg-violet-50 text-violet-700 ring-1 ring-inset ring-violet-200"
          : "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200"
      }`}
    >
      {fusion ? "fusion" : "classic"}
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

  const mutation = useMutation({
    mutationFn: (ingredients: string[]) => suggestDishes(ingredients, avoid),
  });

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
        <h1 className="text-2xl font-bold tracking-tight">What can I make?</h1>
        <p className="mt-1 text-sm text-muted">
          List the ingredients you have and we'll suggest dishes — classic and
          fusion — you can cook right now.
        </p>
      </div>

      <div className="flex flex-col gap-3 rounded-3xl border border-gray-100 bg-surface p-5 shadow-sm">
        <label className="text-sm font-medium text-ink">
          Your ingredients
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
          placeholder="Type an ingredient and press Enter (e.g. palak, paneer, pasta)…"
          className="w-full rounded-2xl border border-gray-200 bg-surface px-4 py-3 text-base outline-none transition focus:border-accent-400 focus:ring-4 focus:ring-accent-100"
        />
        {items.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {items.map((i) => (
              <Chip key={i} label={i} onRemove={() => removeItem(i)} />
            ))}
          </div>
        )}
        <p className="text-xs text-muted">
          We'll assume you also have everyday staples — salt, oil, cumin, chili,
          turmeric, ginger, garlic and onion.
        </p>
        {avoid.length > 0 && (
          <p className="text-xs text-red-600">
            Avoiding: {avoid.join(", ")}.{" "}
            <Link to="/preferences" className="underline">
              Edit
            </Link>
          </p>
        )}
        <div>
          <button
            type="button"
            disabled={items.length === 0 || mutation.isPending}
            onClick={() => mutation.mutate(items)}
            className="rounded-2xl bg-accent-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-accent-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? "Cooking up ideas…" : "Suggest dishes"}
          </button>
        </div>
      </div>

      {mutation.isError && <ErrorBanner />}

      {result && (
        <>
          {result.from_catalog.length > 0 && (
            <section className="flex flex-col gap-3">
              <h2 className="text-lg font-semibold">From our recipes</h2>
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
                          Just need: {m.missing.join(", ")}
                        </span>
                      ) : (
                        <span className="text-xs text-emerald-600">
                          You have everything!
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="flex flex-col gap-3">
            <h2 className="text-lg font-semibold">Ideas to try</h2>
            {result.ideas.length > 0 ? (
              <div className="grid gap-4">
                {result.ideas.map((idea) => (
                  <IdeaCard key={idea.name} idea={idea} />
                ))}
              </div>
            ) : (
              <p className="rounded-2xl border border-dashed border-gray-200 p-6 text-center text-sm text-muted">
                {result.ai_error ?? "No ideas just now — try different ingredients."}
              </p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
