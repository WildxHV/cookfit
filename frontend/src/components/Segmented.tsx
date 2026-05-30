interface SegmentedProps {
  options: string[];
  value: string;
  onChange: (v: string) => void;
}

// Small pill toggle, used for the raw / cooked switch.
export function Segmented({ options, value, onChange }: SegmentedProps) {
  return (
    <div className="inline-flex rounded-xl border border-gray-200 bg-gray-50 p-1">
      {options.map((opt) => (
        <button
          key={opt}
          type="button"
          onClick={() => onChange(opt)}
          className={`rounded-lg px-3 py-1 text-sm font-medium capitalize transition ${
            value === opt
              ? "bg-surface text-accent-700 shadow-sm"
              : "text-muted hover:text-ink"
          }`}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}
