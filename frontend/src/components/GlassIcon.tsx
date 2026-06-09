import { useId } from "react";

/** A stainless-steel Indian glass/tumbler (slightly tapered), side view. */
export function GlassIcon({ className }: { className?: string }) {
  const id = useId();
  const body = `gb-${id}`;
  const rim = `gr-${id}`;
  return (
    <svg viewBox="0 0 36 48" className={className} role="img" aria-label="glass">
      <defs>
        <linearGradient id={body} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#94a3b8" />
          <stop offset="0.25" stopColor="#f1f5f9" />
          <stop offset="0.55" stopColor="#cbd5e1" />
          <stop offset="1" stopColor="#8a97a6" />
        </linearGradient>
        <linearGradient id={rim} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e2e8f0" />
          <stop offset="1" stopColor="#94a3b8" />
        </linearGradient>
      </defs>
      {/* tapered body */}
      <path
        d="M6 8 L30 8 L27 44 Q18 47 9 44 Z"
        fill={`url(#${body})`}
        stroke="#64748b"
        strokeWidth="1.2"
        strokeLinejoin="round"
      />
      {/* rim */}
      <ellipse cx="18" cy="8" rx="12" ry="3.2" fill={`url(#${rim})`} stroke="#64748b" strokeWidth="1.2" />
      <ellipse cx="18" cy="8" rx="9" ry="2" fill="#64748b" opacity="0.5" />
      {/* vertical shine */}
      <rect x="12" y="11" width="2.4" height="30" rx="1.2" fill="#ffffff" opacity="0.6" />
    </svg>
  );
}
