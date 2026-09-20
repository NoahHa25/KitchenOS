import type { Order, OrderStatusUpdate } from "@/types/orders";
import type { Restaurant } from "@/types/restaurants";
import type { SalesSummary } from "@/types/sales";

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
