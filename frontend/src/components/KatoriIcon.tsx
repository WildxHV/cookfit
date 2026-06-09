import { useId } from "react";

/** A stainless-steel katori (round Indian bowl), seen from the TOP — concentric
 *  steel rings with a hollow centre and a soft highlight. */
export function KatoriIcon({ className }: { className?: string }) {
  const id = useId();
  const ring = `kr-${id}`;
  const well = `kw-${id}`;
  return (
    <svg viewBox="0 0 48 48" className={className} role="img" aria-label="katori">
      <defs>
        <linearGradient id={ring} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#f8fafc" />
          <stop offset="0.5" stopColor="#cbd5e1" />
          <stop offset="1" stopColor="#94a3b8" />
        </linearGradient>
        <radialGradient id={well} cx="0.42" cy="0.38" r="0.7">
          <stop offset="0" stopColor="#e2e8f0" />
          <stop offset="0.7" stopColor="#b8c2cf" />
          <stop offset="1" stopColor="#94a3b8" />
        </radialGradient>
      </defs>
      {/* outer rim */}
      <circle cx="24" cy="24" r="22" fill={`url(#${ring})`} stroke="#64748b" strokeWidth="1.2" />
      {/* sloped inner wall */}
      <circle cx="24" cy="24" r="17" fill="#94a3b8" />
      {/* well (bottom of the bowl) */}
      <circle cx="24" cy="24" r="14.5" fill={`url(#${well})`} stroke="#8a97a6" strokeWidth="0.8" />
      {/* highlight crescent on the rim */}
      <path
        d="M9 17 A22 22 0 0 1 31 4"
        fill="none"
        stroke="#ffffff"
        strokeWidth="2"
        strokeLinecap="round"
        opacity="0.75"
      />
    </svg>
  );
}
