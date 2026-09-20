"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { updateOrderStatus } from "@/lib/api/client";

type OrderStatusControlsProps = {
  restaurantId: string;
  orderId: string;
  status: string;
};

const nextActions: Record<
  string,
  {
    status: string;
    label: string;
  }
> = {
  pending: {
    status: "preparing",
    label: "Start Preparing",
  },
  preparing: {
    status: "ready",
    label: "Mark Ready",
  },
  ready: {
    status: "completed",
    label: "Complete Order",
  },
};

export default function OrderStatusControls({
  restaurantId,
  orderId,
  status,
}: OrderStatusControlsProps) {
  const router = useRouter();

  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const action = nextActions[status];

  if (!action) {
    return null;
  }

  async function handleStatusUpdate() {
    setIsUpdating(true);
    setError(null);

    try {
      await updateOrderStatus(restaurantId, orderId, {
        status: action.status,
      });

      router.refresh();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update order status.",
      );
    } finally {
      setIsUpdating(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-semibold text-slate-950">Order Actions</h2>

          <p className="mt-1 text-sm text-slate-500">
            Move this order through the kitchen workflow.
          </p>
        </div>

        <button
          type="button"
          onClick={handleStatusUpdate}
          disabled={isUpdating}
          className="rounded-lg bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUpdating ? "Updating..." : action.label}
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}
    </div>
  );
}
