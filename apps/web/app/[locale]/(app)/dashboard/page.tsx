import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

import {
  getLowStockIngredients,
  getOrders,
  getRestaurants,
  getSalesSummary,
} from "@/lib/api/client";

import LowStockAlert from "@/components/inventory/LowStockAlert";
import OrderStatus from "@/components/dashboard/OrderStatus";
import RecentOrders from "@/components/dashboard/RecentOrders";
import SalesOverview from "@/components/dashboard/SalesOverview";
import StatCard from "@/components/dashboard/StatCard";

export const dynamic = "force-dynamic";

const DEMO_RESTAURANT_SLUG = "kitchenos-demo";

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");

  const restaurants = await getRestaurants();

  const restaurant = restaurants.find(
    (item) => item.slug === DEMO_RESTAURANT_SLUG,
  );

  if (!restaurant) {
    throw new Error("KitchenOS demo restaurant not found.");
  }

  const [orders, salesSummary, lowStockIngredients] = await Promise.all([
    getOrders(restaurant.id),
    getSalesSummary(restaurant.id),
    getLowStockIngredients(restaurant.id),
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
      label: t("completedRevenue"),
      value: new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: "RUB",
        maximumFractionDigits: 2,
      }).format(Number(salesSummary.total_revenue)),
      change: `${salesSummary.total_orders} ${t("completed").toLowerCase()}`,
      description: t("revenueFromCompletedOrders"),
    },
    {
      label: t("totalOrders"),
      value: String(orders.length),
      change: `${orderStatusCounts.pending} ${t("pending").toLowerCase()}`,
      description: t("allOrdersForRestaurant"),
    },
    {
      label: t("averageOrder"),
      value:
        orders.length > 0
          ? new Intl.NumberFormat(undefined, {
              style: "currency",
              currency: "RUB",
              maximumFractionDigits: 2,
            }).format(
              orders.reduce(
                (total, order) => total + Number(order.total_amount),
                0,
              ) / orders.length,
            )
          : new Intl.NumberFormat(undefined, {
              style: "currency",
              currency: "RUB",
              maximumFractionDigits: 2,
            }).format(0),
      change: `${orders.length} ${t("ordersCount")}`,
      description: t("averageValueAcrossOrders"),
    },
    {
      label: t("completedOrders"),
      value: String(orderStatusCounts.completed),
      change:
        orders.length > 0
          ? `${Math.round(
              (orderStatusCounts.completed / orders.length) * 100,
            )}%`
          : "0%",
      description: t("shareOfOrdersCompleted"),
    },
  ];

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {new Intl.DateTimeFormat(undefined, {
              weekday: "long",
              month: "long",
              day: "numeric",
            }).format(new Date())}
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            {t("title")}
          </h1>

          <p className="mt-2 text-slate-500">
            {restaurant.name} · {t("liveOverview")}
          </p>
        </div>

        <Link
          href="/orders"
          className="rounded-lg bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
        >
          {t("viewOrders")}
        </Link>
      </div>

      <LowStockAlert ingredients={lowStockIngredients} />

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
