import { type Product } from "./product";

export interface Order {
    id: number;
    user_id: number;
    product_id: number;
    quantity: number;
    total_price: number;
    status: string;
    created_at: string;
    updated_at?: string;
    product?: Product;
}
