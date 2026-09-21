"use client";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";
import type { Ingredient } from "@/types/inventory";

type LowStockAlertProps = {
  ingredients: Ingredient[];
};

export default function LowStockAlert({ ingredients }: LowStockAlertProps) {
  const t = useTranslations("inventory");

  if (ingredients.length === 0) {
    return null;
  }

  return (
    <section className="rounded-xl border border-red-200 bg-red-50 shadow-sm">
      <div className="flex flex-col gap-4 border-b border-red-200 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
            !
          </div>

          <div>
            <h2 className="font-semibold text-red-950">{t("lowStock")}</h2>

            <p className="mt-1 text-sm text-red-700">
              {ingredients.length}{" "}
              {ingredients.length === 1
                ? t("ingredientNeedsRestock")
                : t("ingredientsNeedRestock")}
            </p>
          </div>
        </div>

        <Link
          href="/inventory"
          className="inline-flex items-center justify-center rounded-lg border border-red-200 bg-white px-4 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-100"
        >
          {t("viewInventory")}
        </Link>
      </div>

      <div className="divide-y divide-red-100">
        {ingredients.map((ingredient) => (
          <div
            key={ingredient.id}
            className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-medium text-red-950">{ingredient.name}</p>

              <p className="mt-1 text-sm text-red-700">
                {t("currentStock")}:{" "}
                <span className="font-semibold">
                  {ingredient.current_stock} {ingredient.unit}
                </span>
              </p>
            </div>

            <div className="text-sm sm:text-end">
              <p className="text-red-700">{t("minimumStock")}</p>

              <p className="mt-1 font-semibold text-red-950">
                {ingredient.minimum_stock} {ingredient.unit}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
