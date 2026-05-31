import { useState } from "react";
import { usePreferences } from "../lib/usePreferences";

export function Preferences() {
  const { avoid, addAvoid, removeAvoid } = usePreferences();
  const [text, setText] = useState("");

  function commit(raw: string) {
    raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .forEach(addAvoid);
    setText("");
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Your preferences</h1>
        <p className="mt-1 text-sm text-muted">
          List anything you're allergic to or simply don't eat. We'll remember it
          on this device and keep it out of your suggestions — and flag any recipe
          that contains it.
        </p>
      </div>

      <div className="flex flex-col gap-3 rounded-3xl border border-gray-100 bg-surface p-5 shadow-sm">
        <label className="text-sm font-medium text-ink">
          Allergens &amp; things you avoid
        </label>
        <input
          value={text}
          onChange={(e) => {
            const v = e.target.value;
            if (v.endsWith(",")) commit(v);
            else setText(v);
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              commit(text);
            } else if (e.key === "Backspace" && !text && avoid.length) {
              removeAvoid(avoid[avoid.length - 1]);
            }
          }}
          placeholder="e.g. peanuts, mushroom, gluten — press Enter to add"
          className="w-full rounded-2xl border border-gray-200 bg-surface px-4 py-3 text-base outline-none transition focus:border-red-300 focus:ring-4 focus:ring-red-100"
        />
        {avoid.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {avoid.map((a) => (
              <span
                key={a}
                className="inline-flex items-center gap-1 rounded-full bg-red-50 px-3 py-1 text-sm font-medium text-red-700"
              >
                {a}
                <button
                  type="button"
                  onClick={() => removeAvoid(a)}
                  className="ml-0.5 text-red-400 hover:text-red-700"
                  aria-label={`Remove ${a}`}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted">
            Nothing added yet — suggestions will include everything.
          </p>
        )}
      </div>
    </div>
  );
}
