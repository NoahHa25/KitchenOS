"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

type WasteModalProps = {
  ingredientName: string;
  unit: string;
  currentStock: number;
  unitCost: number;
  onClose: () => void;
  onSubmit: (quantity: number, reason: string) => Promise<void>;
};

export default function WasteModal({
  ingredientName,
  unit,
  currentStock,
  unitCost,
  onClose,
  onSubmit,
}: WasteModalProps) {
  const t = useTranslations("inventory");
  const commonT = useTranslations("common");

  const [quantity, setQuantity] = useState(0);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const estimatedCost = quantity * unitCost;
  const exceedsStock = quantity > currentStock;

  async function handleSubmit() {
    setError("");

    if (quantity <= 0) {
      setError(t("wasteQuantityInvalid"));
      return;
    }

    if (exceedsStock) {
      setError(t("wasteQuantityExceedsStock"));
      return;
    }

    if (!reason.trim()) {
      setError(t("wasteReasonRequired"));
      return;
    }

    setLoading(true);

    try {
      await onSubmit(quantity, reason.trim());
      onClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : t("wasteRecordFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            {t("recordWaste")}
          </p>

          <h2 className="mt-1 text-xl font-bold text-slate-950">
            {ingredientName}
          </h2>
        </div>

        <div className="mt-6 rounded-xl bg-slate-50 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-500">{t("currentStock")}</span>

            <span className="font-semibold text-slate-900">
              {currentStock} {unit}
            </span>
          </div>

          <div className="mt-3 flex items-center justify-between">
            <span className="text-sm text-slate-500">{t("costPerUnit")}</span>

            <span className="font-semibold text-slate-900">
              {new Intl.NumberFormat(undefined, {
                style: "currency",
                currency: "RUB",
                maximumFractionDigits: 2,
              }).format(unitCost)}
            </span>
          </div>
        </div>

        <div className="mt-6 space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-700">
              {t("quantity")}
            </label>

            <div className="mt-2 flex items-center">
              <input
                type="number"
                min="0"
                max={currentStock}
                step="0.001"
                value={quantity}
                onChange={(event) => setQuantity(Number(event.target.value))}
                className="w-full rounded-lg border border-slate-200 px-3 py-2 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
              />

              <span className="ml-3 text-sm font-medium text-slate-500">
                {unit}
              </span>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700">
              {t("wasteReason")}
            </label>

            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder={t("wasteReasonPlaceholder")}
              rows={3}
              className="mt-2 w-full resize-none rounded-lg border border-slate-200 px-3 py-2 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-100"
            />
          </div>
        </div>

        <div className="mt-6 rounded-xl border border-red-100 bg-red-50 p-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-red-700">
              {t("estimatedWasteCost")}
            </span>

            <span className="text-lg font-bold text-red-700">
              {new Intl.NumberFormat(undefined, {
                style: "currency",
                currency: "RUB",
                maximumFractionDigits: 2,
              }).format(estimatedCost)}
            </span>
          </div>

          <p className="mt-1 text-xs text-red-600">
            {t("estimatedWasteCostDescription")}
          </p>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3">
            <p className="text-sm font-medium text-red-600">{error}</p>
          </div>
        )}

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {commonT("cancel")}
          </button>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? t("recordingWaste") : t("recordWaste")}
          </button>
        </div>
      </div>
    </div>
  );
}
