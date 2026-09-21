import { getTranslations } from "next-intl/server";

import { Link } from "@/i18n/navigation";

import { getIngredients, getRestaurants } from "@/lib/api/client";

import InventoryStats from "@/components/inventory/InventoryStats";
import InventoryTable from "@/components/inventory/InventoryTable";

export const dynamic = "force-dynamic";

const DEMO_RESTAURANT_SLUG = "kitchenos-demo";

export default async function InventoryPage() {
  const t = await getTranslations("inventory");

  const restaurants = await getRestaurants();

  const restaurant = restaurants.find(
    (item) => item.slug === DEMO_RESTAURANT_SLUG,
  );

  if (!restaurant) {
    throw new Error("KitchenOS demo restaurant not found.");
  }

  const ingredients = await getIngredients(restaurant.id);

  const lowStockCount = ingredients.filter(
    (ingredient) => ingredient.current_stock <= ingredient.minimum_stock,
  ).length;

  const inventoryValue = ingredients.reduce(
    (total, ingredient) =>
      total + ingredient.current_stock * Number(ingredient.cost_per_unit),
    0,
  );

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-medium text-slate-500">
            {restaurant.name}
          </p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950">
            {t("title")}
          </h1>

          <p className="mt-2 text-slate-500">{t("description")}</p>
        </div>

        <Link
          href="/dashboard"
          className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
        >
          {t("backToDashboard")}
        </Link>
      </div>

      <InventoryStats
        ingredientCount={ingredients.length}
        lowStockCount={lowStockCount}
        inventoryValue={inventoryValue}
      />

      <InventoryTable restaurantId={restaurant.id} ingredients={ingredients} />
    </div>
  );
}
