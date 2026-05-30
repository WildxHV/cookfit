interface QuantityControlProps {
  quantity: number;
  unit: string;
  unitOptions: string[];
  onQuantityChange: (q: number) => void;
  onUnitChange: (u: string) => void;
}

export function QuantityControl({
  quantity,
  unit,
  unitOptions,
  onQuantityChange,
  onUnitChange,
}: QuantityControlProps) {
  const step = (delta: number) =>
    onQuantityChange(Math.max(0, Math.round((quantity + delta) * 100) / 100));

  return (
    <div className="flex items-stretch gap-2">
      <div className="flex items-stretch rounded-xl border border-gray-200 bg-surface">
        <button
          type="button"
          onClick={() => step(-0.5)}
          className="px-3 text-lg text-muted hover:text-accent-600"
          aria-label="Decrease quantity"
        >
          −
        </button>
        <input
          type="number"
          min={0}
          step={0.5}
          value={quantity}
          onChange={(e) => onQuantityChange(Math.max(0, Number(e.target.value)))}
          className="w-16 border-x border-gray-200 bg-transparent text-center text-base outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none"
        />
        <button
          type="button"
          onClick={() => step(0.5)}
          className="px-3 text-lg text-muted hover:text-accent-600"
          aria-label="Increase quantity"
        >
          +
        </button>
      </div>
      <select
        value={unit}
        onChange={(e) => onUnitChange(e.target.value)}
        className="rounded-xl border border-gray-200 bg-surface px-3 text-sm outline-none focus:border-accent-400"
      >
        {unitOptions.map((u) => (
          <option key={u} value={u}>
            {u}
          </option>
        ))}
      </select>
    </div>
  );
}
