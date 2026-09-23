"use client";

import { useEffect, useState } from "react";
import { Link } from "@/i18n/navigation";

import {
  getIngredients,
  getRecipe,
  getRecipeFoodCost,
  getRecipeIngredients,
  getRestaurants,
} from "@/lib/api/client";

import FoodCostCard from "@/components/recipes/FoodCostCard";
import RecipeEditForm from "@/components/recipes/RecipeEditForm";
import RecipeIngredients from "@/components/recipes/RecipeIngredients";

import type { Ingredient } from "@/types/inventory";
import type { FoodCost, Recipe, RecipeIngredient } from "@/types/recipes";

type RecipeDetailsPageProps = {
  params: Promise<{
    locale: string;
    recipeId: string;
  }>;
};

export default function RecipeDetailsPage({ params }: RecipeDetailsPageProps) {
  const [recipeId, setRecipeId] = useState<string | null>(null);
  const [restaurantId, setRestaurantId] = useState<string | null>(null);

  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [recipeIngredients, setRecipeIngredients] = useState<
    RecipeIngredient[]
  >([]);
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [foodCost, setFoodCost] = useState<FoodCost | null>(null);

  const [editing, setEditing] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadRecipeData(
    currentRestaurantId: string,
    currentRecipeId: string,
  ) {
    const [recipeData, recipeIngredientData, ingredientData, foodCostData] =
      await Promise.all([
        getRecipe(currentRestaurantId, currentRecipeId),
        getRecipeIngredients(currentRestaurantId, currentRecipeId),
        getIngredients(currentRestaurantId),
        getRecipeFoodCost(currentRestaurantId, currentRecipeId),
      ]);

    setRecipe(recipeData);
    setRecipeIngredients(recipeIngredientData);
    setIngredients(ingredientData);
    setFoodCost(foodCostData);
  }

  useEffect(() => {
    let cancelled = false;

    async function initialize() {
      try {
        setLoading(true);
        setError(null);

        const { recipeId: currentRecipeId } = await params;

        const restaurants = await getRestaurants();
        const restaurant = restaurants[0];

        if (!restaurant) {
          throw new Error("No restaurant found.");
        }

        if (cancelled) return;

        setRecipeId(currentRecipeId);
        setRestaurantId(restaurant.id);

        await loadRecipeData(restaurant.id, currentRecipeId);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load recipe.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    initialize();

    return () => {
      cancelled = true;
    };
  }, [params]);

  async function handleChanged() {
    if (!restaurantId || !recipeId) return;

    try {
      await loadRecipeData(restaurantId, recipeId);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to refresh recipe.",
      );
    }
  }

  function handleRecipeSaved(updatedRecipe: Recipe) {
    setRecipe(updatedRecipe);
    setEditing(false);
  }

  if (loading) {
    return (
      <main className="p-8">
        <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-sm">
          <p className="text-sm font-medium text-slate-500">
            Loading recipe...
          </p>
        </div>
      </main>
    );
  }

  if (error || !recipe || !restaurantId || !recipeId || !foodCost) {
    return (
      <main className="p-8">
        <div className="rounded-2xl border border-red-200 bg-white p-12 text-center shadow-sm">
          <h1 className="text-lg font-bold text-slate-950">
            Unable to load recipe
          </h1>

          <p className="mt-2 text-sm text-red-600">
            {error ?? "Recipe not found."}
          </p>

          <Link
            href="/recipes"
            className="mt-6 inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            Back to Recipes
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-8 p-8">
      <div>
        <Link
          href="/recipes"
          className="text-sm font-medium text-slate-500 transition hover:text-slate-900"
        >
          ← Back to Recipes
        </Link>

        <div className="mt-6 flex flex-col justify-between gap-6 md:flex-row md:items-start">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-slate-950">
                {recipe.name}
              </h1>

              <span
                className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                  recipe.is_active
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-slate-100 text-slate-500"
                }`}
              >
                {recipe.is_active ? "Active" : "Inactive"}
              </span>
            </div>

            <p className="mt-2 max-w-2xl text-slate-500">
              {recipe.description || "No description provided."}
            </p>
          </div>

          <button
            type="button"
            onClick={() => setEditing((current) => !current)}
            className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
          >
            {editing ? "Close Editor" : "Edit Recipe"}
          </button>
        </div>
      </div>

      {editing && (
        <RecipeEditForm
          restaurantId={restaurantId}
          recipe={recipe}
          onSaved={handleRecipeSaved}
          onCancel={() => setEditing(false)}
        />
      )}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Selling Price
          </p>

          <p className="mt-2 text-2xl font-bold text-slate-950">
            {Number(recipe.selling_price).toFixed(2)} RUB
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Food Cost
          </p>

          <p className="mt-2 text-2xl font-bold text-slate-950">
            {Number(foodCost.food_cost).toFixed(2)} RUB
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Estimated Profit
          </p>

          <p className="mt-2 text-2xl font-bold text-emerald-600">
            {(
              Number(recipe.selling_price) - Number(foodCost.food_cost)
            ).toFixed(2)}{" "}
            RUB
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Margin
          </p>

          <p className="mt-2 text-2xl font-bold text-slate-950">
            {Number(recipe.selling_price) > 0
              ? (
                  ((Number(recipe.selling_price) - Number(foodCost.food_cost)) /
                    Number(recipe.selling_price)) *
                  100
                ).toFixed(0)
              : "0"}
            %
          </p>
        </div>
      </section>

      <RecipeIngredients
        restaurantId={restaurantId}
        recipeId={recipe.id}
        recipeIngredients={recipeIngredients}
        ingredients={ingredients}
        onChanged={handleChanged}
      />

      <FoodCostCard
        foodCost={foodCost}
        sellingPrice={Number(recipe.selling_price)}
      />

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-slate-900 p-2 text-white">✨</div>

          <div>
            <h2 className="text-lg font-bold text-slate-950">AI Insights</h2>

            <p className="text-sm text-slate-500">
              This panel will become the intelligence layer of KitchenOS.
            </p>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="font-medium text-slate-900">
              Ingredient price monitoring
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Future versions will automatically detect supplier price
              increases.
            </p>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="font-medium text-slate-900">Margin protection</p>

            <p className="mt-1 text-sm text-slate-500">
              KitchenOS will recommend new selling prices when food costs
              change.
            </p>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
            <p className="font-medium text-slate-900">
              Purchasing intelligence
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Forecast ingredient demand from future orders and historical
              usage.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
