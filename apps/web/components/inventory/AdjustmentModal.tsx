"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";

type AdjustmentModalProps = {
  ingredientName: string;
  unit: string;
  currentStock: number;
  unitCost: number;
  onClose: () => void;
  onSubmit: (targetStock: number, reason: string) => Promise<void>;
};

export default function AdjustmentModal({
  ingredientName,
  unit,
  currentStock,
  unitCost,
  onClose,
  onSubmit,
}: AdjustmentModalProps) {
  const t = useTranslations("inventory");
  const commonT = useTranslations("common");

  const [targetStock, setTargetStock] = useState(currentStock);
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const difference = useMemo(
    () => targetStock - currentStock,
    [targetStock, currentStock],
  );

  const valueImpact = useMemo(
    () => Math.abs(difference) * unitCost,
    [difference, unitCost],
  );

  async function handleSubmit() {
    setError("");

    if (targetStock < 0) {
      setError(t("adjustmentNegativeStock"));
      return;
    }

    if (!reason.trim()) {
      setError(t("adjustmentReasonRequired"));
      return;
    }

    setLoading(true);

    try {
      await onSubmit(targetStock, reason.trim());
      onClose();
    } catch {
      setError(t("adjustmentFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <h2 className="text-xl font-bold">
          {t("adjustStock")} — {ingredientName}
        </h2>

        <div className="mt-6 space-y-4">
          <div className="rounded-lg bg-slate-50 p-4">
            <p className="text-sm text-slate-500">{t("currentStock")}</p>

            <p className="mt-1 text-2xl font-bold">
              {currentStock} {unit}
            </p>
          </div>

          <div>
            <label className="text-sm font-medium">{t("countedStock")}</label>

            <input
              type="number"
              min="0"
              step="0.001"
              value={targetStock}
              onChange={(e) => setTargetStock(Number(e.target.value))}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2"
            />
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <div className="flex justify-between text-sm">
              <span>{t("difference")}</span>

              <span
                className={
                  difference > 0
                    ? "font-semibold text-emerald-600"
                    : difference < 0
                      ? "font-semibold text-red-600"
                      : "font-semibold text-slate-600"
                }
              >
                {difference > 0 ? "+" : ""}
                {difference.toFixed(3)} {unit}
              </span>
            </div>

            <div className="mt-3 flex justify-between text-sm">
              <span>{t("estimatedValueImpact")}</span>

              <span className="font-semibold">
                {valueImpact.toFixed(2)} RUB
              </span>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium">
              {t("adjustmentReason")}
            </label>

            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={t("adjustmentReasonPlaceholder")}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2"
              rows={3}
            />
          </div>

          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}
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
            {loading ? t("updating") : t("saveAdjustment")}
          </button>
        </div>
      </div>
    </div>
  );
}
