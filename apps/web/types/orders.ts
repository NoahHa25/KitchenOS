export type OrderItem = {
  id: string;
  order_id: string;
  recipe_id: string;
  quantity: string;
  unit_price: string;
};

export type Order = {
  id: string;
  restaurant_id: string;
  status: string;
  total_amount: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
};

export type OrderStatusUpdate = {
  status: string;
};
