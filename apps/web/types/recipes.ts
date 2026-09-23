export type Recipe = {
  id: string;
  restaurant_id: string;
  name: string;
  description: string | null;
  selling_price: string;
  portion_size: number;
  portion_unit: string;
  is_active: boolean;
};

export type RecipeCreate = {
  restaurant_id: string;
  name: string;
  description?: string | null;
  selling_price?: number;
  portion_size?: number;
  portion_unit?: string;
  is_active?: boolean;
};

export type RecipeUpdate = {
  name?: string;
  description?: string | null;
  selling_price?: number;
  portion_size?: number;
  portion_unit?: string;
  is_active?: boolean;
};

export type RecipeIngredient = {
  id: string;
  recipe_id: string;
  ingredient_id: string;
  quantity: number;
};

export type RecipeIngredientCreate = {
  ingredient_id: string;
  quantity: number;
};

export type RecipeIngredientUpdate = {
  quantity: number;
};

export type FoodCostBreakdownItem = {
  ingredient: string;
  quantity: number;
  cost_per_unit: number;
  total_cost: number;
};

export type FoodCost = {
  recipe_id: string;
  recipe_name: string;
  food_cost: number;
  breakdown: FoodCostBreakdownItem[];
};
