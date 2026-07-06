export interface Product {
    id: string;
    name: string;
    brand: string;
    category: string;
    description: string;
    price: number;
    originalPrice?: number;
    stock: number;
    image_url?: string;
    image?: string;
    rating?: number;
    reviewsCount?: number;
    specifications?: Record<string, string>;
    kind?: string;
    season?: string;
}