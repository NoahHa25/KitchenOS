"use client";

import { useTranslations } from "next-intl";

type StockBadgeProps = {
  current: number;
  minimum: number;
};

export default function StockBadge({ current, minimum }: StockBadgeProps) {
  const t = useTranslations("inventory");

  const low = current <= minimum;

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
        low ? "bg-red-100 text-red-700" : "bg-emerald-100 text-emerald-700"
      }`}
    >
      {low ? t("lowStock") : t("inStock")}
    </span>
  );
}
