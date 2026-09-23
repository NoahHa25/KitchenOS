"use client";

import type { FoodCost } from "@/types/recipes";

type FoodCostCardProps = {
  foodCost: FoodCost;
  sellingPrice: number;
};

export default function FoodCostCard({
  foodCost,
  sellingPrice,
}: FoodCostCardProps) {
  const totalFoodCost = Number(foodCost.food_cost);
  const foodCostPercentage =
    sellingPrice > 0 ? (totalFoodCost / sellingPrice) * 100 : 0;

  const grossProfit = sellingPrice - totalFoodCost;

  function formatCurrency(value: number) {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: "RUB",
      maximumFractionDigits: 2,
    }).format(value);
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Cost Analysis
          </p>

          <h2 className="mt-1 text-xl font-bold text-slate-950">Food Cost</h2>
        </div>

        <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-700">
          {foodCostPercentage.toFixed(1)}%
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Food Cost
          </p>

          <p className="mt-1 text-xl font-bold text-slate-950">
            {formatCurrency(totalFoodCost)}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Selling Price
          </p>

          <p className="mt-1 text-xl font-bold text-slate-950">
            {formatCurrency(sellingPrice)}
          </p>
        </div>

        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Gross Profit
          </p>

          <p className="mt-1 text-xl font-bold text-slate-950">
            {formatCurrency(grossProfit)}
          </p>
        </div>
      </div>

      <div className="mt-8">
        <h3 className="text-sm font-semibold text-slate-900">
          Ingredient Breakdown
        </h3>

        {foodCost.breakdown.length === 0 ? (
          <div className="mt-4 rounded-xl border border-dashed border-slate-300 p-6 text-center">
            <p className="text-sm text-slate-500">
              No ingredients have been added to this recipe yet.
            </p>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                  <th className="pb-3 pr-4">Ingredient</th>
                  <th className="pb-3 pr-4">Quantity</th>
                  <th className="pb-3 pr-4">Cost / Unit</th>
                  <th className="pb-3 text-right">Total</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {foodCost.breakdown.map((item) => (
                  <tr key={`${item.ingredient}-${item.quantity}`}>
                    <td className="py-3 pr-4 font-medium text-slate-900">
                      {item.ingredient}
                    </td>

                    <td className="py-3 pr-4 text-slate-600">
                      {item.quantity}
                    </td>

                    <td className="py-3 pr-4 text-slate-600">
                      {formatCurrency(Number(item.cost_per_unit))}
                    </td>

                    <td className="py-3 text-right font-semibold text-slate-900">
                      {formatCurrency(Number(item.total_cost))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
