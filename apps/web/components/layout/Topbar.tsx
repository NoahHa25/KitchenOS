"use client";

import { useLocale, useTranslations } from "next-intl";

import { usePathname, useRouter } from "@/i18n/navigation";

const locales = [
  { value: "en", label: "English" },
  { value: "ru", label: "Русский" },
  { value: "ar", label: "العربية" },
  { value: "es", label: "Español" },
] as const;

export default function Topbar() {
  const dashboardT = useTranslations("dashboard");
  const commonT = useTranslations("common");

  const locale = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  function handleLocaleChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const nextLocale = event.target.value;

    router.replace(pathname, {
      locale: nextLocale,
    });
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-6 backdrop-blur lg:px-8">
      <div>
        <p className="text-sm font-medium text-slate-500">
          {dashboardT("restaurantOperations")}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <label className="sr-only" htmlFor="language-selector">
          {commonT("language")}
        </label>

        <select
          id="language-selector"
          value={locale}
          onChange={handleLocaleChange}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
        >
          {locales.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>

        <div className="hidden text-end sm:block">
          <p className="text-sm font-medium text-slate-900">Admin</p>

          <p className="text-xs text-slate-500">Restaurant Manager</p>
        </div>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
          A
        </div>
      </div>
    </header>
  );
}
