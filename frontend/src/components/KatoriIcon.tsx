import { useId } from "react";

/** A small stainless-steel katori (the round Indian bowl), side view. */
export function KatoriIcon({ className }: { className?: string }) {
  const id = useId();
  const steel = `steel-${id}`;
  const rim = `rim-${id}`;
  return (
    <svg
      viewBox="0 0 48 34"
      className={className}
      role="img"
      aria-label="katori"
    >
      <defs>
        <linearGradient id={steel} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#f1f5f9" />
          <stop offset="0.45" stopColor="#cbd5e1" />
          <stop offset="1" stopColor="#94a3b8" />
        </linearGradient>
        <linearGradient id={rim} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e2e8f0" />
          <stop offset="1" stopColor="#94a3b8" />
        </linearGradient>
      </defs>
      {/* bowl body */}
      <path
        d="M5 11 C7 28 41 28 43 11 Z"
        fill={`url(#${steel})`}
        stroke="#64748b"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      {/* shine on the body */}
      <path
        d="M12 14 C13 22 16 25 19 26"
        fill="none"
        stroke="#f8fafc"
        strokeWidth="1.4"
        strokeLinecap="round"
        opacity="0.7"
      />
      {/* outer rim */}
      <ellipse
        cx="24"
        cy="11"
        rx="19"
        ry="5"
        fill={`url(#${rim})`}
        stroke="#64748b"
        strokeWidth="1.2"
      />
      {/* hollow */}
      <ellipse cx="24" cy="11" rx="14.5" ry="3.4" fill="#64748b" opacity="0.55" />
      <ellipse cx="24" cy="10.4" rx="14.5" ry="3.1" fill="#cbd5e1" />
    </svg>
  );
}
