"use client";

import { useState } from "react";

import { updateRecipe } from "@/lib/api/client";

import type { Recipe } from "@/types/recipes";

type RecipeEditFormProps = {
  restaurantId: string;
  recipe: Recipe;
  onSaved: (recipe: Recipe) => void;
  onCancel: () => void;
};

export default function RecipeEditForm({
  restaurantId,
  recipe,
  onSaved,
  onCancel,
}: RecipeEditFormProps) {
  const [name, setName] = useState(recipe.name);
  const [description, setDescription] = useState(recipe.description ?? "");
  const [sellingPrice, setSellingPrice] = useState(
    String(recipe.selling_price),
  );
  const [portionSize, setPortionSize] = useState(String(recipe.portion_size));
  const [portionUnit, setPortionUnit] = useState(recipe.portion_unit);
  const [isActive, setIsActive] = useState(recipe.is_active);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!name.trim()) {
      setError("Recipe name is required.");
      return;
    }

    const parsedSellingPrice = Number(sellingPrice);
    const parsedPortionSize = Number(portionSize);

    if (!Number.isFinite(parsedSellingPrice) || parsedSellingPrice < 0) {
      setError("Selling price must be zero or greater.");
      return;
    }

    if (!Number.isFinite(parsedPortionSize) || parsedPortionSize <= 0) {
      setError("Portion size must be greater than zero.");
      return;
    }

    if (!portionUnit.trim()) {
      setError("Portion unit is required.");
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const updatedRecipe = await updateRecipe(restaurantId, recipe.id, {
        name: name.trim(),
        description: description.trim() || null,
        selling_price: parsedSellingPrice,
        portion_size: parsedPortionSize,
        portion_unit: portionUnit.trim(),
        is_active: isActive,
      });

      onSaved(updatedRecipe);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update recipe.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Recipe Management
        </p>

        <h2 className="mt-1 text-xl font-bold text-slate-950">Edit Recipe</h2>

        <p className="mt-2 text-sm text-slate-500">
          Update the recipe details and selling information.
        </p>
      </div>

      {error && (
        <div className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <label
              htmlFor="recipe-name"
              className="block text-sm font-medium text-slate-700"
            >
              Recipe Name
            </label>

            <input
              id="recipe-name"
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
              disabled={saving}
            />
          </div>

          <div>
            <label
              htmlFor="recipe-selling-price"
              className="block text-sm font-medium text-slate-700"
            >
              Selling Price
            </label>

            <input
              id="recipe-selling-price"
              type="number"
              min="0"
              step="0.01"
              value={sellingPrice}
              onChange={(event) => setSellingPrice(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
              disabled={saving}
            />
          </div>

          <div className="md:col-span-2">
            <label
              htmlFor="recipe-description"
              className="block text-sm font-medium text-slate-700"
            >
              Description
            </label>

            <textarea
              id="recipe-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              rows={4}
              className="mt-2 w-full resize-none rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
              disabled={saving}
            />
          </div>

          <div>
            <label
              htmlFor="recipe-portion-size"
              className="block text-sm font-medium text-slate-700"
            >
              Portion Size
            </label>

            <input
              id="recipe-portion-size"
              type="number"
              min="0.001"
              step="0.001"
              value={portionSize}
              onChange={(event) => setPortionSize(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
              disabled={saving}
            />
          </div>

          <div>
            <label
              htmlFor="recipe-portion-unit"
              className="block text-sm font-medium text-slate-700"
            >
              Portion Unit
            </label>

            <input
              id="recipe-portion-unit"
              type="text"
              value={portionUnit}
              onChange={(event) => setPortionUnit(event.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
              disabled={saving}
            />
          </div>
        </div>

        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(event) => setIsActive(event.target.checked)}
            disabled={saving}
            className="h-4 w-4 rounded border-slate-300"
          />

          <span className="text-sm font-medium text-slate-700">
            Recipe is active
          </span>
        </label>

        <div className="flex justify-end gap-3 border-t border-slate-100 pt-6">
          <button
            type="button"
            onClick={onCancel}
            disabled={saving}
            className="rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </form>
    </section>
  );
}
