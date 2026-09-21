"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

type RestockModalProps = {
  ingredientName: string;
  onClose: () => void;
  onSubmit: (quantity: number, unitCost: number) => Promise<void>;
};

export default function RestockModal({
  ingredientName,
  onClose,
  onSubmit,
}: RestockModalProps) {
  const t = useTranslations("inventory");
  const commonT = useTranslations("common");

  const [quantity, setQuantity] = useState(0);
  const [unitCost, setUnitCost] = useState(0);
  const [loading, setLoading] = useState(false);

  async function handleSubmit() {
    if (quantity <= 0) return;

    setLoading(true);

    try {
      await onSubmit(quantity, unitCost);
      onClose();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="text-xl font-bold">
          {t("restock")} — {ingredientName}
        </h2>

        <div className="mt-6 space-y-4">
          <div>
            <label className="text-sm font-medium">{t("quantity")}</label>

            <input
              type="number"
              min="0"
              step="0.001"
              value={quantity}
              onChange={(event) => setQuantity(Number(event.target.value))}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>

          <div>
            <label className="text-sm font-medium">{t("unitCost")}</label>

            <input
              type="number"
              min="0"
              step="0.01"
              value={unitCost}
              onChange={(event) => setUnitCost(Number(event.target.value))}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={loading}
            className="rounded-lg border px-4 py-2 disabled:opacity-50"
          >
            {commonT("cancel")}
          </button>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="rounded-lg bg-slate-900 px-4 py-2 text-white disabled:opacity-50"
          >
            {loading ? t("updating") : t("restock")}
          </button>
        </div>
      </div>
    </div>
  );
}
