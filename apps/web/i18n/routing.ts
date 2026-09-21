import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["en", "ru", "ar", "es"],
  defaultLocale: "en",
  localePrefix: "always",
});
