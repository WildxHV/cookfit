export function ErrorBanner({ message }: { message?: string }) {
  return (
    <div className="rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm text-red-700">
      {message ?? "Something went wrong. Is the backend running on port 8000?"}
    </div>
  );
}
