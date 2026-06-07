import { useI18n } from "../lib/i18n";

export function ErrorBanner({ message }: { message?: string }) {
  const { t } = useI18n();
  return (
    <div className="rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm text-red-700">
      {message ?? t("common.error")}
    </div>
  );
}
