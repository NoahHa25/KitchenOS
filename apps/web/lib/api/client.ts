import type { Order, OrderStatusUpdate } from "@/types/orders";
import type { Restaurant } from "@/types/restaurants";
import type { SalesSummary } from "@/types/sales";
import type { Ingredient, IngredientUpdate } from "@/types/inventory";

import type {
  InventoryMovement,
  InventoryMovementCreate,
} from "@/types/inventory-movements";

import type {
  FoodCost,
  Recipe,
  RecipeCreate,
  RecipeIngredient,
  RecipeIngredientCreate,
  RecipeIngredientUpdate,
  RecipeUpdate,
} from "@/types/recipes";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let message = `API request failed with status ${response.status}`;

    try {
      const error = await response.json();

      if (typeof error?.detail === "string") {
        message = error.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function getRestaurants(): Promise<Restaurant[]> {
  return apiFetch<Restaurant[]>("/restaurants");
}

export async function getOrders(restaurantId: string): Promise<Order[]> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Order[]>(`/orders?${params.toString()}`);
}

export async function getSalesSummary(
  restaurantId: string,
): Promise<SalesSummary> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<SalesSummary>(`/orders/sales/summary?${params.toString()}`);
}

export async function getOrder(
  restaurantId: string,
  orderId: string,
): Promise<Order> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Order>(`/orders/${orderId}?${params.toString()}`);
}

export async function updateOrderStatus(
  restaurantId: string,
  orderId: string,
  data: OrderStatusUpdate,
): Promise<Order> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Order>(`/orders/${orderId}/status?${params.toString()}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getIngredients(
  restaurantId: string,
): Promise<Ingredient[]> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Ingredient[]>(`/ingredients?${params.toString()}`);
}

export async function getIngredient(
  restaurantId: string,
  ingredientId: string,
): Promise<Ingredient> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Ingredient>(
    `/ingredients/${ingredientId}?${params.toString()}`,
  );
}

export async function getLowStockIngredients(
  restaurantId: string,
): Promise<Ingredient[]> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Ingredient[]>(`/ingredients/low-stock?${params.toString()}`);
}

export async function updateIngredient(
  restaurantId: string,
  ingredientId: string,
  data: IngredientUpdate,
): Promise<Ingredient> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Ingredient>(
    `/ingredients/${ingredientId}?${params.toString()}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    },
  );
}

export async function deleteIngredient(
  restaurantId: string,
  ingredientId: string,
): Promise<void> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  await apiFetch(`/ingredients/${ingredientId}?${params.toString()}`, {
    method: "DELETE",
  });
}

export async function createInventoryMovement(
  restaurantId: string,
  data: InventoryMovementCreate,
): Promise<InventoryMovement> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<InventoryMovement>(
    `/inventory-movements?${params.toString()}`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export async function getInventoryMovements(
  restaurantId: string,
  ingredientId: string,
): Promise<InventoryMovement[]> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
    ingredient_id: ingredientId,
  });

  return apiFetch<InventoryMovement[]>(
    `/inventory-movements?${params.toString()}`,
  );
}

export async function getRecipes(restaurantId: string): Promise<Recipe[]> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Recipe[]>(`/recipes?${params.toString()}`);
}

export async function getRecipe(
  restaurantId: string,
  recipeId: string,
): Promise<Recipe> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Recipe>(`/recipes/${recipeId}?${params.toString()}`);
}

export async function createRecipe(data: RecipeCreate): Promise<Recipe> {
  return apiFetch<Recipe>("/recipes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateRecipe(
  restaurantId: string,
  recipeId: string,
  data: RecipeUpdate,
): Promise<Recipe> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<Recipe>(`/recipes/${recipeId}?${params.toString()}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteRecipe(
  restaurantId: string,
  recipeId: string,
): Promise<void> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  await apiFetch(`/recipes/${recipeId}?${params.toString()}`, {
    method: "DELETE",
  });
}

export async function getRecipeIngredients(
  restaurantId: string,
  recipeId: string,
): Promise<RecipeIngredient[]> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<RecipeIngredient[]>(
    `/recipes/${recipeId}/ingredients?${params.toString()}`,
  );
}

export async function addRecipeIngredient(
  restaurantId: string,
  recipeId: string,
  data: RecipeIngredientCreate,
): Promise<RecipeIngredient> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<RecipeIngredient>(
    `/recipes/${recipeId}/ingredients?${params.toString()}`,
    {
      method: "POST",
      body: JSON.stringify(data),
    },
  );
}

export async function updateRecipeIngredient(
  restaurantId: string,
  recipeId: string,
  recipeIngredientId: string,
  data: RecipeIngredientUpdate,
): Promise<RecipeIngredient> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<RecipeIngredient>(
    `/recipes/${recipeId}/ingredients/${recipeIngredientId}?${params.toString()}`,
    {
      method: "PATCH",
      body: JSON.stringify(data),
    },
  );
}

export async function deleteRecipeIngredient(
  restaurantId: string,
  recipeId: string,
  recipeIngredientId: string,
): Promise<void> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  await apiFetch(
    `/recipes/${recipeId}/ingredients/${recipeIngredientId}?${params.toString()}`,
    {
      method: "DELETE",
    },
  );
}

export async function getRecipeFoodCost(
  restaurantId: string,
  recipeId: string,
): Promise<FoodCost> {
  const params = new URLSearchParams({
    restaurant_id: restaurantId,
  });

  return apiFetch<FoodCost>(
    `/recipes/${recipeId}/food-cost?${params.toString()}`,
  );
}
