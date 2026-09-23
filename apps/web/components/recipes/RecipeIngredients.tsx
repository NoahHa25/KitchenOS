"use client";

import { useState } from "react";

import {
  addRecipeIngredient,
  deleteRecipeIngredient,
  updateRecipeIngredient,
} from "@/lib/api/client";

import type { Ingredient } from "@/types/inventory";
import type { RecipeIngredient } from "@/types/recipes";

type RecipeIngredientsProps = {
  restaurantId: string;
  recipeId: string;
  recipeIngredients: RecipeIngredient[];
  ingredients: Ingredient[];
  onChanged: () => Promise<void>;
};

export default function RecipeIngredients({
  restaurantId,
  recipeId,
  recipeIngredients,
  ingredients,
  onChanged,
}: RecipeIngredientsProps) {
  const [selectedIngredientId, setSelectedIngredientId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingQuantity, setEditingQuantity] = useState("");
  const [error, setError] = useState<string | null>(null);

  const availableIngredients = ingredients.filter(
    (ingredient) =>
      !recipeIngredients.some(
        (recipeIngredient) => recipeIngredient.ingredient_id === ingredient.id,
      ),
  );

  function getIngredient(ingredientId: string) {
    return ingredients.find((ingredient) => ingredient.id === ingredientId);
  }

  async function handleAdd() {
    if (!selectedIngredientId || !quantity) {
      setError("Select an ingredient and enter a quantity.");
      return;
    }

    const parsedQuantity = Number(quantity);

    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setError("Quantity must be greater than zero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await addRecipeIngredient(restaurantId, recipeId, {
        ingredient_id: selectedIngredientId,
        quantity: parsedQuantity,
      });

      setSelectedIngredientId("");
      setQuantity("");

      await onChanged();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to add ingredient.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdate(recipeIngredientId: string) {
    const parsedQuantity = Number(editingQuantity);

    if (!Number.isFinite(parsedQuantity) || parsedQuantity <= 0) {
      setError("Quantity must be greater than zero.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await updateRecipeIngredient(restaurantId, recipeId, recipeIngredientId, {
        quantity: parsedQuantity,
      });

      setEditingId(null);
      setEditingQuantity("");

      await onChanged();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update ingredient.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(recipeIngredientId: string) {
    setLoading(true);
    setError(null);

    try {
      await deleteRecipeIngredient(restaurantId, recipeId, recipeIngredientId);

      await onChanged();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to remove ingredient.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Recipe Composition
        </p>

        <h2 className="mt-1 text-xl font-bold text-slate-950">Ingredients</h2>
      </div>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      <div className="mt-6 grid gap-3 md:grid-cols-[1fr_160px_auto]">
        <select
          value={selectedIngredientId}
          onChange={(event) => setSelectedIngredientId(event.target.value)}
          className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
        >
          <option value="">Select ingredient</option>

          {availableIngredients.map((ingredient) => (
            <option key={ingredient.id} value={ingredient.id}>
              {ingredient.name} ({ingredient.unit})
            </option>
          ))}
        </select>

        <input
          type="number"
          min="0.001"
          step="0.001"
          value={quantity}
          onChange={(event) => setQuantity(event.target.value)}
          placeholder="Quantity"
          className="rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
        />

        <button
          type="button"
          onClick={handleAdd}
          disabled={loading}
          className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Saving..." : "Add Ingredient"}
        </button>
      </div>

      <div className="mt-8 overflow-x-auto">
        {recipeIngredients.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center">
            <p className="text-sm text-slate-500">No ingredients added yet.</p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                <th className="pb-3 pr-4">Ingredient</th>
                <th className="pb-3 pr-4">Unit</th>
                <th className="pb-3 pr-4">Quantity</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100">
              {recipeIngredients.map((recipeIngredient) => {
                const ingredient = getIngredient(
                  recipeIngredient.ingredient_id,
                );

                const isEditing = editingId === recipeIngredient.id;

                return (
                  <tr key={recipeIngredient.id}>
                    <td className="py-4 pr-4 font-medium text-slate-900">
                      {ingredient?.name ?? "Unknown ingredient"}
                    </td>

                    <td className="py-4 pr-4 text-slate-600">
                      {ingredient?.unit ?? "—"}
                    </td>

                    <td className="py-4 pr-4">
                      {isEditing ? (
                        <input
                          type="number"
                          min="0.001"
                          step="0.001"
                          value={editingQuantity}
                          onChange={(event) =>
                            setEditingQuantity(event.target.value)
                          }
                          className="w-32 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-slate-400"
                        />
                      ) : (
                        <span className="text-slate-700">
                          {recipeIngredient.quantity}
                        </span>
                      )}
                    </td>

                    <td className="py-4 text-right">
                      <div className="flex justify-end gap-2">
                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => handleUpdate(recipeIngredient.id)}
                              disabled={loading}
                              className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
                            >
                              Save
                            </button>

                            <button
                              type="button"
                              onClick={() => {
                                setEditingId(null);
                                setEditingQuantity("");
                              }}
                              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => {
                                setEditingId(recipeIngredient.id);
                                setEditingQuantity(
                                  String(recipeIngredient.quantity),
                                );
                                setError(null);
                              }}
                              className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
                            >
                              Edit
                            </button>

                            <button
                              type="button"
                              onClick={() => handleDelete(recipeIngredient.id)}
                              disabled={loading}
                              className="rounded-lg border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                            >
                              Remove
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
