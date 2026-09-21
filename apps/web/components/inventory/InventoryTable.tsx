"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import {
  createInventoryMovement,
  getInventoryMovements,
} from "@/lib/api/client";

import type { Ingredient } from "@/types/inventory";
import type { InventoryMovement } from "@/types/inventory-movements";

import MovementHistory from "./MovementHistory";
import RestockModal from "./RestockModal";
import StockBadge from "./StockBadge";

type InventoryTableProps = {
  restaurantId: string;
  ingredients: Ingredient[];
};

export default function InventoryTable({
  restaurantId,
  ingredients,
}: InventoryTableProps) {
  const t = useTranslations("inventory");
  const commonT = useTranslations("common");

  const [selected, setSelected] = useState<Ingredient | null>(null);
  const [historyIngredient, setHistoryIngredient] = useState<Ingredient | null>(
    null,
  );
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(false);
  const [rows, setRows] = useState(ingredients);

  function formatCurrency(value: number) {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: "RUB",
      maximumFractionDigits: 2,
    }).format(value);
  }

  async function handleRestock(quantity: number, unitCost: number) {
    if (!selected) return;

    await createInventoryMovement(restaurantId, {
      ingredient_id: selected.id,
      movement_type: "purchase",
      quantity,
      unit_cost: unitCost,
      reason: "Manual restock",
    });

    setRows((current) =>
      current.map((ingredient) =>
        ingredient.id === selected.id
          ? {
              ...ingredient,
              current_stock: ingredient.current_stock + quantity,
            }
          : ingredient,
      ),
    );
  }

  async function handleViewHistory(ingredient: Ingredient) {
    setHistoryIngredient(ingredient);
    setMovements([]);
    setHistoryError(false);
    setHistoryLoading(true);

    try {
      const history = await getInventoryMovements(restaurantId, ingredient.id);

      setMovements(history);
    } catch {
      setHistoryError(true);
    } finally {
      setHistoryLoading(false);
    }
  }

  function closeHistory() {
    setHistoryIngredient(null);
    setMovements([]);
    setHistoryError(false);
  }

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full">
          <thead className="bg-slate-50">
            <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <th className="px-6 py-4">{t("name")}</th>
              <th className="px-6 py-4">{t("unit")}</th>
              <th className="px-6 py-4">{t("currentStock")}</th>
              <th className="px-6 py-4">{t("minimumStock")}</th>
              <th className="px-6 py-4">{t("costPerUnit")}</th>
              <th className="px-6 py-4">{t("status")}</th>
              <th className="px-6 py-4">{t("actions")}</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {rows.map((ingredient) => (
              <tr key={ingredient.id} className="hover:bg-slate-50">
                <td className="px-6 py-4 font-medium text-slate-900">
                  {ingredient.name}
                </td>

                <td className="px-6 py-4 text-slate-600">{ingredient.unit}</td>

                <td className="px-6 py-4">{ingredient.current_stock}</td>

                <td className="px-6 py-4">{ingredient.minimum_stock}</td>

                <td className="px-6 py-4">
                  {formatCurrency(Number(ingredient.cost_per_unit))}
                </td>

                <td className="px-6 py-4">
                  <StockBadge
                    current={ingredient.current_stock}
                    minimum={ingredient.minimum_stock}
                  />
                </td>

                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => handleViewHistory(ingredient)}
                      className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium transition hover:bg-slate-100"
                    >
                      {t("viewHistory")}
                    </button>

                    <button
                      onClick={() => setSelected(ingredient)}
                      className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-slate-800"
                    >
                      {t("restock")}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && (
        <RestockModal
          ingredientName={selected.name}
          onClose={() => setSelected(null)}
          onSubmit={handleRestock}
        />
      )}

      {historyIngredient && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/40 p-4">
          <div className="flex min-h-full items-center justify-center">
            <div className="w-full max-w-3xl">
              <div className="mb-3 flex items-center justify-between rounded-xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    {t("ingredients")}
                  </p>

                  <h2 className="text-lg font-bold text-slate-950">
                    {historyIngredient.name}
                  </h2>
                </div>

                <button
                  onClick={closeHistory}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100"
                >
                  {commonT("cancel")}
                </button>
              </div>

              {historyLoading ? (
                <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                  <p className="text-sm font-medium text-slate-500">
                    {commonT("loading")}
                  </p>
                </div>
              ) : historyError ? (
                <div className="rounded-xl border border-red-200 bg-white p-8 text-center shadow-sm">
                  <p className="text-sm font-medium text-red-600">
                    {t("movementHistoryLoadFailed")}
                  </p>
                </div>
              ) : (
                <MovementHistory movements={movements} />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
