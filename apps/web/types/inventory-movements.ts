export type InventoryMovement = {
  id: string;
  ingredient_id: string;
  movement_type: string;
  quantity: string;
  unit_cost: string;
  reason: string | null;
  created_at: string;
};

export type InventoryMovementCreate = {
  ingredient_id: string;
  movement_type: string;
  quantity: number;
  unit_cost?: number;
  reason?: string;
};
