"use client";

import { useLocale, useTranslations } from "next-intl";

import type { InventoryMovement } from "@/types/inventory-movements";

type MovementHistoryProps = {
  movements: InventoryMovement[];
};

const movementStyles: Record<string, string> = {
  purchase: "bg-emerald-50 text-emerald-700",
  sale: "bg-blue-50 text-blue-700",
  waste: "bg-red-50 text-red-700",
  adjustment: "bg-amber-50 text-amber-700",
};

const movementSymbols: Record<string, string> = {
  purchase: "+",
  sale: "−",
  waste: "−",
  adjustment: "↕",
};

export default function MovementHistory({ movements }: MovementHistoryProps) {
  const t = useTranslations("inventory");
  const locale = useLocale();

  function formatDate(value: string) {
    return new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  }

  if (movements.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <p className="text-sm font-medium text-slate-700">
          {t("noMovementHistory")}
        </p>

        <p className="mt-1 text-sm text-slate-400">
          {t("noMovementHistoryDescription")}
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-5">
        <h2 className="font-semibold text-slate-950">{t("movementHistory")}</h2>

        <p className="mt-1 text-sm text-slate-500">
          {t("movementHistoryDescription")}
        </p>
      </div>

      <div className="divide-y divide-slate-100">
        {movements.map((movement) => {
          const style =
            movementStyles[movement.movement_type] ??
            "bg-slate-100 text-slate-700";

          const symbol = movementSymbols[movement.movement_type] ?? "•";

          return (
            <div
              key={movement.id}
              className="flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-start gap-4">
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg font-bold ${style}`}
                >
                  {symbol}
                </div>

                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold capitalize text-slate-900">
                      {t(`movementTypes.${movement.movement_type}`)}
                    </p>

                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${style}`}
                    >
                      {movement.quantity}
                    </span>
                  </div>

                  {movement.reason && (
                    <p className="mt-1 text-sm text-slate-500">
                      {movement.reason}
                    </p>
                  )}

                  <p className="mt-2 text-xs text-slate-400">
                    {formatDate(movement.created_at)}
                  </p>
                </div>
              </div>

              <div className="sm:text-end">
                <p className="text-xs font-medium text-slate-400">
                  {t("unitCost")}
                </p>

                <p className="mt-1 font-semibold text-slate-900">
                  {new Intl.NumberFormat(locale, {
                    style: "currency",
                    currency: "RUB",
                    maximumFractionDigits: 2,
                  }).format(Number(movement.unit_cost))}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
