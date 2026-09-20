import Link from "next/link";
import { notFound } from "next/navigation";

import { getOrder, getRestaurants } from "@/lib/api/client";

import OrderStatusControls from "@/components/orders/OrderStatusControls";

const DEMO_RESTAURANT_SLUG = "kitchenos-demo";

const statusStyles: Record<string, string> = {
  pending: "bg-amber-50 text-amber-700 ring-amber-600/20",
  preparing: "bg-blue-50 text-blue-700 ring-blue-600/20",
  ready: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  completed: "bg-slate-100 text-slate-700 ring-slate-500/20",
  cancelled: "bg-red-50 text-red-700 ring-red-600/20",
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
    month: "long",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

type OrderDetailsPageProps = {
  params: Promise<{
    orderId: string;
  }>;
};

export default async function OrderDetailsPage({
  params,
}: OrderDetailsPageProps) {
  const { orderId } = await params;

  const restaurants = await getRestaurants();

  const restaurant = restaurants.find(
    (item) => item.slug === DEMO_RESTAURANT_SLUG,
  );

  if (!restaurant) {
    throw new Error("KitchenOS demo restaurant not found.");
  }

  let order;

  try {
    order = await getOrder(restaurant.id, orderId);
  } catch {
    notFound();
  }

  const statusClass =
    statusStyles[order.status] ??
    "bg-slate-100 text-slate-700 ring-slate-500/20";

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <Link
            href="/orders"
            className="text-sm font-semibold text-slate-500 transition hover:text-slate-950"
          >
            ← Back to Orders
          </Link>

          <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-950">
            Order #{order.id.slice(0, 8)}
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Created {formatDate(order.created_at)}
          </p>
        </div>

        <span
          className={`inline-flex w-fit rounded-full px-3 py-1.5 text-sm font-semibold capitalize ring-1 ring-inset ${statusClass}`}
        >
          {order.status}
        </span>
      </div>

      <section className="grid gap-6 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Order Total</p>

          <p className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
            {formatCurrency(order.total_amount)}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Items</p>

          <p className="mt-2 text-2xl font-bold tracking-tight text-slate-950">
            {order.items.length}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-medium text-slate-500">Current Status</p>

          <p className="mt-2 text-2xl font-bold capitalize tracking-tight text-slate-950">
            {order.status}
          </p>
        </div>
      </section>

      <OrderStatusControls
        restaurantId={restaurant.id}
        orderId={order.id}
        status={order.status}
      />

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 className="font-semibold text-slate-950">Order Items</h2>

          <p className="mt-1 text-sm text-slate-500">
            Recipes and quantities included in this order.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[650px] text-left">
            <thead className="border-b border-slate-100 bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Recipe
                </th>

                <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Quantity
                </th>

                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Unit Price
                </th>

                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Line Total
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {order.items.map((item) => {
                const lineTotal =
                  Number(item.quantity) * Number(item.unit_price);

                return (
                  <tr key={item.id}>
                    <td className="px-6 py-4">
                      <p className="text-sm font-semibold text-slate-950">
                        Recipe #{item.recipe_id.slice(0, 8)}
                      </p>

                      <p className="mt-1 text-xs text-slate-400">
                        {item.recipe_id}
                      </p>
                    </td>

                    <td className="px-6 py-4 text-sm text-slate-600">
                      {item.quantity}
                    </td>

                    <td className="px-6 py-4 text-right text-sm text-slate-600">
                      {formatCurrency(item.unit_price)}
                    </td>

                    <td className="px-6 py-4 text-right text-sm font-semibold text-slate-950">
                      {formatCurrency(String(lineTotal))}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex justify-end border-t border-slate-200 px-6 py-5">
          <div className="w-full max-w-xs">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-slate-500">Total</span>

              <span className="text-xl font-bold text-slate-950">
                {formatCurrency(order.total_amount)}
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-semibold text-slate-950">Order Information</h2>

        <dl className="mt-5 grid gap-5 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Order ID
            </dt>

            <dd className="mt-1 break-all text-sm text-slate-700">
              {order.id}
            </dd>
          </div>

          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Restaurant ID
            </dt>

            <dd className="mt-1 break-all text-sm text-slate-700">
              {order.restaurant_id}
            </dd>
          </div>

          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Created
            </dt>

            <dd className="mt-1 text-sm text-slate-700">
              {formatDate(order.created_at)}
            </dd>
          </div>

          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Last Updated
            </dt>

            <dd className="mt-1 text-sm text-slate-700">
              {formatDate(order.updated_at)}
            </dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
