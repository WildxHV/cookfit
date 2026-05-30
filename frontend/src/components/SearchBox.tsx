import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useDebounce } from "../lib/useDebounce";

interface SearchBoxProps<T> {
  placeholder: string;
  queryKey: string;
  search: (q: string) => Promise<T[]>;
  getKey: (item: T) => string | number;
  renderItem: (item: T) => React.ReactNode;
  onSelect: (item: T) => void;
  // Optional AI fallback shown when the DB search returns no matches.
  aiSearch?: (q: string) => Promise<{ slug: string }>;
  onAiResult?: (slug: string) => void;
  aiNoun?: string; // e.g. "ingredient" | "dish"
}

export function SearchBox<T>({
  placeholder,
  queryKey,
  search,
  getKey,
  renderItem,
  onSelect,
  aiSearch,
  onAiResult,
  aiNoun = "item",
}: SearchBoxProps<T>) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const debounced = useDebounce(text.trim(), 200);

  const { data, isLoading } = useQueryCompat(queryKey, debounced, search);
  const settled = !isLoading && data !== undefined;
  const showAi = !!aiSearch && settled;

  async function runAi() {
    if (!aiSearch || !onAiResult) return;
    setAiBusy(true);
    setAiError(null);
    try {
      const result = await aiSearch(debounced);
      onAiResult(result.slug);
      setText("");
      setOpen(false);
    } catch (err) {
      setAiError(aiErrorMessage(err, aiNoun));
    } finally {
      setAiBusy(false);
    }
  }

  return (
    <div className="relative">
      <input
        value={text}
        onChange={(e) => {
          setText(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        placeholder={placeholder}
        className="w-full rounded-2xl border border-gray-200 bg-surface px-5 py-3.5 text-base shadow-sm outline-none transition focus:border-accent-400 focus:ring-4 focus:ring-accent-100"
      />
      {open && debounced.length > 0 && (
        <ul className="absolute z-10 mt-2 max-h-72 w-full overflow-auto rounded-2xl border border-gray-100 bg-surface p-1 shadow-lg">
          {isLoading && (
            <li className="px-4 py-3 text-sm text-muted">Searching…</li>
          )}
          {settled && data.length === 0 && !aiSearch && (
            <li className="px-4 py-3 text-sm text-muted">No matches.</li>
          )}
          {data?.map((item) => (
            <li key={getKey(item)}>
              <button
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault();
                  onSelect(item);
                  setText("");
                  setOpen(false);
                }}
                className="w-full rounded-xl px-4 py-2.5 text-left text-sm hover:bg-accent-50"
              >
                {renderItem(item)}
              </button>
            </li>
          ))}
          {showAi && (
            <li className={data.length > 0 ? "mt-1 border-t border-gray-100 pt-1" : ""}>
              {aiBusy ? (
                <div className="flex items-center gap-2 px-4 py-3 text-sm text-muted">
                  <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-accent-300 border-t-transparent" />
                  Searching with AI for “{debounced}”…
                </div>
              ) : (
                <button
                  type="button"
                  onMouseDown={(e) => {
                    e.preventDefault();
                    void runAi();
                  }}
                  className="flex w-full items-center gap-2 rounded-xl px-4 py-3 text-left text-sm text-accent-700 hover:bg-accent-50"
                >
                  <span aria-hidden>✨</span>
                  <span>
                    {data.length > 0 ? "Not it? " : "Not in our list — "}
                    look up{" "}
                    <span className="font-medium">“{debounced}”</span> with AI
                  </span>
                </button>
              )}
              {aiError && (
                <p className="px-4 pb-2 text-xs text-red-600">{aiError}</p>
              )}
            </li>
          )}
        </ul>
      )}
    </div>
  );
}

function aiErrorMessage(err: unknown, noun: string): string {
  const status = (err as { response?: { status?: number } })?.response?.status;
  if (status === 422)
    return `Couldn't find reliable data for this ${noun}.`;
  if (status === 503) return "AI lookup isn't configured on the server.";
  if (status === 502) return "The AI service is unavailable right now.";
  return "Something went wrong with the AI lookup. Please try again.";
}

function useQueryCompat<T>(
  key: string,
  q: string,
  search: (q: string) => Promise<T[]>,
) {
  const query = useQuery({
    queryKey: [key, q],
    queryFn: () => search(q),
    enabled: q.length > 0,
  });
  return {
    data: query.data,
    isLoading: query.isLoading && query.fetchStatus !== "idle",
  };
}
