export type Ingredient = {
  id: string;
  restaurant_id: string;
  name: string;
  unit: string;
  current_stock: number;
  minimum_stock: number;
  cost_per_unit: number;
  created_at: string;
  updated_at: string;
};

export type IngredientUpdate = {
  name?: string;
  unit?: string;
  current_stock?: number;
  minimum_stock?: number;
  cost_per_unit?: number;
};
