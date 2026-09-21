import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

type OrderStatusProps = {
  counts: {
    pending: number;
    preparing: number;
    ready: number;
    completed: number;
  };
};

const statuses = [
  {
    key: "pending",
    dot: "bg-amber-400",
  },
  {
    key: "preparing",
    dot: "bg-blue-500",
  },
  {
    key: "ready",
    dot: "bg-emerald-500",
  },
  {
    key: "completed",
    dot: "bg-slate-400",
  },
] as const;

export default function OrderStatus({ counts }: OrderStatusProps) {
  const t = useTranslations("dashboard");
  const statusT = useTranslations("status");

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-6 py-5">
        <h2 className="font-semibold text-slate-950">{t("orderStatus")}</h2>

        <p className="mt-1 text-sm text-slate-500">
          {t("currentOrdersAcrossRestaurant")}
        </p>
      </div>

      <div className="divide-y divide-slate-100">
        {statuses.map((status) => (
          <div
            key={status.key}
            className="flex items-center justify-between px-6 py-4"
          >
            <div className="flex items-center gap-3">
              <span className={`h-2.5 w-2.5 rounded-full ${status.dot}`} />

              <span className="text-sm font-medium text-slate-700">
                {statusT(status.key)}
              </span>
            </div>

            <span className="text-lg font-semibold text-slate-950">
              {counts[status.key]}
            </span>
          </div>
        ))}
      </div>

      <div className="border-t border-slate-200 p-6">
        <Link
          href="/orders"
          className="block w-full rounded-lg border border-slate-200 px-4 py-2.5 text-center text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
        >
          {t("viewOrders")}
        </Link>
      </div>
    </div>
  );
}
