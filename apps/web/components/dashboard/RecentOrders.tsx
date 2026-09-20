import type { Order } from "@/types/orders";

type RecentOrdersProps = {
  orders: Order[];
};

const statusStyles: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700 ring-amber-600/20",
  preparing: "bg-blue-50 text-blue-700 ring-blue-600/20",
  ready: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  completed: "bg-slate-100 text-slate-700 ring-slate-500/20",
};

function formatCurrency(value: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function RecentOrders({ orders }: RecentOrdersProps) {
  const recentOrders = [...orders]
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    )
    .slice(0, 5);

  return (
    <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col justify-between gap-3 border-b border-slate-200 px-6 py-5 sm:flex-row sm:items-center">
        <div>
          <h2 className="font-semibold text-slate-950">Recent Orders</h2>

          <p className="mt-1 text-sm text-slate-500">
            Latest activity from your restaurant.
          </p>
        </div>

        <a
          href="/orders"
          className="text-sm font-semibold text-slate-700 transition hover:text-slate-950"
        >
          View all
        </a>
      </div>

      {recentOrders.length === 0 ? (
        <div className="px-6 py-12 text-center text-sm text-slate-400">
          No orders yet.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Order
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Time
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Items
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Status
                </th>

                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Total
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {recentOrders.map((order) => (
                <tr key={order.id} className="transition hover:bg-slate-50">
                  <td className="px-6 py-4 text-sm font-semibold text-slate-950">
                    #{order.id.slice(0, 8)}
                  </td>

                  <td className="px-6 py-4 text-sm text-slate-600">
                    {formatTime(order.created_at)}
                  </td>

                  <td className="px-6 py-4 text-sm text-slate-600">
                    {order.items.length}{" "}
                    {order.items.length === 1 ? "item" : "items"}
                  </td>

                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${
                        statusStyles[order.status] ??
                        "bg-slate-100 text-slate-700 ring-slate-500/20"
                      }`}
                    >
                      {order.status}
                    </span>
                  </td>

                  <td className="px-6 py-4 text-right text-sm font-semibold text-slate-950">
                    {formatCurrency(order.total_amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
