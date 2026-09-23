import { Link } from "@/i18n/navigation";
import { getRecipes, getRestaurants } from "@/lib/api/client";

export default async function RecipesPage() {
  const restaurants = await getRestaurants();

  const restaurant = restaurants[0];

  if (!restaurant) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold text-slate-950">Recipes</h1>
        <p className="mt-2 text-slate-500">No restaurant found.</p>
      </div>
    );
  }

  const recipes = await getRecipes(restaurant.id);

  const totalRecipes = recipes.length;
  const activeRecipes = recipes.filter((r) => r.is_active).length;

  const averagePrice =
    totalRecipes === 0
      ? 0
      : recipes.reduce((sum, recipe) => sum + Number(recipe.selling_price), 0) /
        totalRecipes;

  return (
    <main className="space-y-8 p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-slate-400">
            KitchenOS
          </p>

          <h1 className="mt-1 text-3xl font-bold text-slate-950">
            Recipe Dashboard
          </h1>

          <p className="mt-2 text-slate-500">
            Manage recipes, monitor pricing, and prepare for AI-powered food
            cost optimization.
          </p>
        </div>

        <button className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">
          + New Recipe
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Total Recipes
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-950">
            {totalRecipes}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Active
          </p>

          <p className="mt-2 text-3xl font-bold text-emerald-600">
            {activeRecipes}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
            Average Price
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-950">
            {averagePrice.toFixed(2)} RUB
          </p>
        </div>
      </div>

      {recipes.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
          <h2 className="text-lg font-semibold text-slate-900">
            No recipes yet
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Create your first recipe to start managing food costs.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {recipes.map((recipe) => (
            <article
              key={recipe.id}
              className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:shadow-lg"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-950">
                    {recipe.name}
                  </h2>

                  <p className="mt-1 line-clamp-2 text-sm text-slate-500">
                    {recipe.description || "No description available."}
                  </p>
                </div>

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

              <div className="mt-6 grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Selling Price
                  </p>

                  <p className="mt-1 font-bold text-slate-950">
                    {Number(recipe.selling_price).toFixed(2)} RUB
                  </p>
                </div>

                <div className="rounded-xl bg-slate-50 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    Portion
                  </p>

                  <p className="mt-1 font-bold text-slate-950">
                    {recipe.portion_size} {recipe.portion_unit}
                  </p>
                </div>
              </div>

              <div className="mt-5 rounded-xl border border-dashed border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                  Food Cost
                </p>

                <p className="mt-1 font-semibold text-slate-500">
                  Coming in Sprint 5
                </p>
              </div>

              <div className="mt-6 flex gap-2">
                <Link
                  href={`/recipes/${recipe.id}`}
                  className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-center text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                >
                  View
                </Link>

                <button className="flex-1 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800">
                  Edit
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
