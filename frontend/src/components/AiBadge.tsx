// Transient "just added" badge, shown only on the result the user just looked
// up (added to the catalog). It does not persist for later searches/users.
export function AiBadge() {
  return (
    <span
      title="Just added to your catalog"
      className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-2 py-0.5 text-xs font-medium text-violet-700 ring-1 ring-inset ring-violet-200"
    >
      <span aria-hidden>✨</span>
      New
    </span>
  );
}
