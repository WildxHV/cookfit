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
}

export function SearchBox<T>({
  placeholder,
  queryKey,
  search,
  getKey,
  renderItem,
  onSelect,
}: SearchBoxProps<T>) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const debounced = useDebounce(text.trim(), 200);

  const { data, isLoading } = useQueryCompat(queryKey, debounced, search);

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
          {!isLoading && data && data.length === 0 && (
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
        </ul>
      )}
    </div>
  );
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
