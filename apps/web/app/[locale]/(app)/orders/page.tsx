import { Link } from "@/i18n/navigation";

import { getOrders, getRestaurants } from "@/lib/api/client";

const DEMO_RESTAURANT_SLUG = "kitchenos-demo";

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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export default async function OrdersPage() {
  const restaurants = await getRestaurants();

  const restaurant = restaurants.find(
    (item) => item.slug === DEMO_RESTAURANT_SLUG,
  );

  if (!restaurant) {
    throw new Error("KitchenOS demo restaurant not found.");
  }

  const orders = await getOrders(restaurant.id);

  const sortedOrders = [...orders].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  );

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {restaurant.name}
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Orders
          </h1>

          <p className="mt-2 text-slate-500">
            Manage and monitor orders across your restaurant.
          </p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 shadow-sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
            Total Orders
          </p>

          <p className="mt-1 text-lg font-bold text-slate-950">
            {orders.length}
          </p>
        </div>
      </div>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-5">
          <div>
            <h2 className="font-semibold text-slate-950">All Orders</h2>

            <p className="mt-1 text-sm text-slate-500">
              Latest orders from your restaurant.
            </p>
          </div>

          <span className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
            Live
          </span>
        </div>

        {sortedOrders.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <p className="text-sm font-medium text-slate-700">No orders yet</p>

            <p className="mt-1 text-sm text-slate-400">
              Orders will appear here once they are created.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px] text-left">
              <thead className="border-b border-slate-100 bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Order
                  </th>

                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Created
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

                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Action
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100">
                {sortedOrders.map((order) => (
                  <tr key={order.id} className="transition hover:bg-slate-50">
                    <td className="px-6 py-4">
                      <p className="text-sm font-semibold text-slate-950">
                        #{order.id.slice(0, 8)}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">{order.id}</p>
                    </td>

                    <td className="px-6 py-4 text-sm text-slate-600">
                      {formatDate(order.created_at)}
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

                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/orders/${order.id}`}
                        className="text-sm font-semibold text-slate-700 transition hover:text-slate-950"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
