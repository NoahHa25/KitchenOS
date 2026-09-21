import { useLocale, useTranslations } from "next-intl";

type SalesOverviewProps = {
  data: {
    label: string;
    value: number;
    percentage: number;
  }[];
};

export default function SalesOverview({ data }: SalesOverviewProps) {
  const t = useTranslations("dashboard");
  const locale = useLocale();

  function formatCurrency(value: number) {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: "RUB",
      maximumFractionDigits: 2,
    }).format(value);
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
        <div>
          <h2 className="font-semibold text-slate-950">
            {t("recentOrderRevenue")}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {t("revenueFromLatestOrders")}
          </p>
        </div>

        <span className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
          {t("live")}
        </span>
      </div>

      <div className="p-6">
        {data.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-slate-400">
            {t("noOrdersYet")}
          </div>
        ) : (
          <div className="flex h-64 items-end gap-3">
            {data.map((item) => (
              <div
                key={item.label}
                className="flex flex-1 flex-col items-center gap-3"
              >
                <div className="flex h-full w-full items-end">
                  <div
                    className="w-full rounded-t-md bg-slate-900 transition hover:bg-slate-700"
                    style={{
                      height: `${item.percentage}%`,
                    }}
                    title={`${item.label}: ${formatCurrency(item.value)}`}
                  />
                </div>

                <span className="text-xs text-slate-400">{item.label}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
