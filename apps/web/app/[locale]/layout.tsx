import { NextIntlClientProvider } from "next-intl";

export default function LocaleLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <NextIntlClientProvider>{children}</NextIntlClientProvider>;
}
