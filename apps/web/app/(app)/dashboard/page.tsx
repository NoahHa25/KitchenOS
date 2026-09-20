import { getOrders, getRestaurants, getSalesSummary } from "@/lib/api/client";

import OrderStatus from "@/components/dashboard/OrderStatus";
import RecentOrders from "@/components/dashboard/RecentOrders";
import SalesOverview from "@/components/dashboard/SalesOverview";
import StatCard from "@/components/dashboard/StatCard";

export const dynamic = "force-dynamic";

const DEMO_RESTAURANT_SLUG = "kitchenos-demo";

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatDate(date: Date) {
  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(date);
}

export default async function DashboardPage() {
  const restaurants = await getRestaurants();

  const restaurant = restaurants.find(
    (item) => item.slug === DEMO_RESTAURANT_SLUG,
  );

  if (!restaurant) {
    throw new Error("KitchenOS demo restaurant not found.");
  }

  const [orders, salesSummary] = await Promise.all([
    getOrders(restaurant.id),
    getSalesSummary(restaurant.id),
  ]);

  const orderStatusCounts = {
    pending: orders.filter((order) => order.status === "pending").length,
    preparing: orders.filter((order) => order.status === "preparing").length,
    ready: orders.filter((order) => order.status === "ready").length,
    completed: orders.filter((order) => order.status === "completed").length,
  };

  const salesData = [...orders]
    .sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    )
    .slice(-7)
    .map((order) => ({
      label: `#${order.id.slice(0, 4)}`,
      value: Number(order.total_amount),
    }));

  const maxSalesValue = Math.max(...salesData.map((item) => item.value), 1);

  const normalizedSalesData = salesData.map((item) => ({
    ...item,
    percentage: Math.max((item.value / maxSalesValue) * 100, 8),
  }));

  const stats = [
    {
      label: "Completed Revenue",
      value: formatCurrency(salesSummary.total_revenue),
      change: `${salesSummary.total_orders} completed`,
      description: "Revenue from completed orders",
    },
    {
      label: "Total Orders",
      value: String(orders.length),
      change: `${orderStatusCounts.pending} pending`,
      description: "All orders for this restaurant",
    },
    {
      label: "Average Order",
      value:
        orders.length > 0
          ? formatCurrency(
              orders.reduce(
                (total, order) => total + Number(order.total_amount),
                0,
              ) / orders.length,
            )
          : formatCurrency("0"),
      change: `${orders.length} orders`,
      description: "Average value across all orders",
    },
    {
      label: "Completed Orders",
      value: String(orderStatusCounts.completed),
      change:
        orders.length > 0
          ? `${Math.round(
              (orderStatusCounts.completed / orders.length) * 100,
            )}%`
          : "0%",
      description: "Share of orders completed",
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {formatDate(new Date())}
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            Dashboard
          </h1>

          <p className="mt-2 text-slate-500">
            {restaurant.name} · Live operational overview
          </p>
        </div>

        <a
          href="/orders"
          className="rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
        >
          View Orders
        </a>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <SalesOverview data={normalizedSalesData} />
        <OrderStatus counts={orderStatusCounts} />
      </section>

      <RecentOrders orders={orders} />
    </div>
  );
}
