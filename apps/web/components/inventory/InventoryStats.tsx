"use client";

import { useLocale, useTranslations } from "next-intl";

type InventoryStatsProps = {
  ingredientCount: number;
  lowStockCount: number;
  inventoryValue: number;
};

export default function InventoryStats({
  ingredientCount,
  lowStockCount,
  inventoryValue,
}: InventoryStatsProps) {
  const locale = useLocale();
  const t = useTranslations("inventory");

  const stats = [
    {
      label: t("inventoryValue"),
      value: new Intl.NumberFormat(locale, {
        style: "currency",
        currency: "RUB",
        maximumFractionDigits: 2,
      }).format(inventoryValue),
    },
    {
      label: t("ingredients"),
      value: String(ingredientCount),
    },
    {
      label: t("lowStock"),
      value: String(lowStockCount),
    },
  ];

  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
        >
          <p className="text-sm font-medium text-slate-500">{stat.label}</p>

          <p className="mt-3 text-2xl font-bold tracking-tight text-slate-950">
            {stat.value}
          </p>
        </div>
      ))}
    </section>
  );
}
