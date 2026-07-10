import api from "./axios";
import { MOCK_PRODUCTS } from "../utils/mockData";

export const normalizeProductImage = (img: string | undefined | null): string => {
    if (!img || img === "null" || img === "undefined" || img === "") {
        return "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?auto=format&fit=crop&q=80&w=600";
    }
    if (img.startsWith("/uploads")) {
        return `${import.meta.env.VITE_API_URL}${img}`;
    }
    if (img.startsWith("uploads")) {
        return `${import.meta.env.VITE_API_URL}${img}`;
    }
    return img;
};

export const getProducts = async () => {
    let dbProducts = [];
    try {
        const response = await api.get("/products/");
        dbProducts = response.data;
    } catch (err) {
        console.error("API getProducts failed, using localStorage fallback:", err);
        const local = localStorage.getItem("products");
        if (local) {
            const list = JSON.parse(local);
            return list.map((p: any) => ({
                ...p,
                image: normalizeProductImage(p.image_url || p.image)
            }));
        }
        const mockNormalized = MOCK_PRODUCTS.map((p: any) => ({
            ...p,
            image: normalizeProductImage(p.image_url || p.image)
        }));
        localStorage.setItem("products", JSON.stringify(mockNormalized));
        return mockNormalized;
    }

    // Merge any offline/custom local products with db products
    const local = localStorage.getItem("products");
    const localProducts = local ? JSON.parse(local) : [];

    if (dbProducts.length === 0) {
        // If DB has no products, merge local products with MOCK_PRODUCTS
        const merged = localProducts.length > 0 ? localProducts : MOCK_PRODUCTS;
        const normalizedMerged = merged.map((p: any) => ({
            ...p,
            image: normalizeProductImage(p.image_url || p.image)
        }));
        localStorage.setItem("products", JSON.stringify(normalizedMerged));
        return normalizedMerged;
    }

    // If DB has products, merge local custom products that are not already in DB
    const mockProductNames = new Set(MOCK_PRODUCTS.map((p: any) => p.name.toLowerCase()));
    const customLocalProducts = localProducts.filter((p: any) => !mockProductNames.has(p.name.toLowerCase()));

    if (customLocalProducts.length > 0) {
        const dbProductNames = new Set(dbProducts.map((p: any) => p.name.toLowerCase()));
        const newCustomProducts = customLocalProducts.filter((p: any) => !dbProductNames.has(p.name.toLowerCase()));

        if (newCustomProducts.length > 0) {
            // Attempt to upload new offline products to backend in background
            for (const p of newCustomProducts) {
                try {
                    await api.post("/products/", {
                        name: p.name,
                        brand: p.brand || "",
                        category: p.category || "Uncategorized",
                        description: p.description || "",
                        price: p.price,
                        stock: p.stock || 50,
                        image_url: p.image || p.image_url || ""
                    });
                } catch (e) {
                    console.error("Background product sync failed for:", p.name, e);
                }
            }
            // Re-fetch products from DB to get correct IDs and updated list
            try {
                const response = await api.get("/products/");
                dbProducts = response.data;
            } catch (e) {
                dbProducts = [...newCustomProducts, ...dbProducts];
            }
        }
    }

    // Update localStorage with normalized DB products + any remaining custom ones
    const dbProductNames = new Set(dbProducts.map((p: any) => p.name.toLowerCase()));
    const finalCustomProducts = customLocalProducts.filter((p: any) => !dbProductNames.has(p.name.toLowerCase()));
    
    // Normalize dbProducts to match the frontend shape
    const normalizedDb = dbProducts.map((p: any) => ({
        ...p,
        id: p.id.toString(),
        image: normalizeProductImage(p.image_url || p.image)
    }));

    const normalizedCustom = finalCustomProducts.map((p: any) => ({
        ...p,
        image: normalizeProductImage(p.image_url || p.image)
    }));

    const mergedList = [...normalizedCustom, ...normalizedDb];
    localStorage.setItem("products", JSON.stringify(mergedList));
    return mergedList;
};

export const getProductById = async (id: string | number) => {
    try {
        const response = await api.get(`/products/${id}`);
        const p = response.data;
        return {
            ...p,
            id: p.id.toString(),
            image: normalizeProductImage(p.image_url || p.image)
        };
    } catch (err) {
        console.error(`API getProductById ${id} failed, finding in local storage:`, err);
        const local = localStorage.getItem("products");
        if (local) {
            const products = JSON.parse(local);
            const found = products.find((p: any) => p.id.toString() === id.toString());
            if (found) return found;
        }
        throw err;
    }
};

export const createProduct = async (data: any) => {
    try {
        const response = await api.post("/products/", data);
        const newProduct = response.data;

        // Keep local storage in sync
        const local = localStorage.getItem("products");
        const products = local ? JSON.parse(local) : [...MOCK_PRODUCTS];
        const filtered = products.filter((p: any) => p.name.toLowerCase() !== newProduct.name.toLowerCase());
        
        filtered.unshift({
            ...newProduct,
            id: newProduct.id.toString(),
            image: normalizeProductImage(newProduct.image_url || newProduct.image)
        });
        localStorage.setItem("products", JSON.stringify(filtered));

        return newProduct;
    } catch (err) {
        console.error("API createProduct failed, saving to local storage as fallback:", err);
        
        const local = localStorage.getItem("products");
        const products = local ? JSON.parse(local) : [...MOCK_PRODUCTS];
        
        const newProduct = {
            id: `prod-${Date.now()}`,
            name: data.name,
            brand: data.brand || "",
            category: data.category || "Uncategorized",
            price: data.price || 0,
            stock: data.stock || 50,
            rating: 5.0,
            reviewsCount: 0,
            image: normalizeProductImage(data.image_url || data.image),
            description: data.description || ""
        };

        const filtered = products.filter((p: any) => p.name.toLowerCase() !== newProduct.name.toLowerCase());
        filtered.unshift(newProduct);
        localStorage.setItem("products", JSON.stringify(filtered));

        throw err; // Re-throw so callers know there was a network/API issue
    }
};

export const updateProduct = async (id: string | number, data: any) => {
    try {
        const response = await api.put(`/products/${id}`, data);
        const updatedProduct = response.data;

        // Keep local storage in sync
        const local = localStorage.getItem("products");
        if (local) {
            const products = JSON.parse(local);
            const index = products.findIndex((p: any) => p.id.toString() === id.toString());
            if (index !== -1) {
                products[index] = {
                    ...products[index],
                    ...updatedProduct,
                    id: updatedProduct.id.toString(),
                    image: normalizeProductImage(updatedProduct.image_url || updatedProduct.image || products[index].image)
                };
                localStorage.setItem("products", JSON.stringify(products));
            }
        }
        return updatedProduct;
    } catch (err) {
        console.error(`API updateProduct ${id} failed, updating local storage fallback:`, err);
        const local = localStorage.getItem("products");
        if (local) {
            const products = JSON.parse(local);
            const index = products.findIndex((p: any) => p.id.toString() === id.toString());
            if (index !== -1) {
                products[index] = {
                    ...products[index],
                    ...data,
                };
                localStorage.setItem("products", JSON.stringify(products));
            }
        }
        return data; // Return data on fallback to keep UI consistent
    }
};

export const deleteProduct = async (id: string | number) => {
    try {
        await api.delete(`/products/${id}`);
    } catch (err) {
        console.error(`API deleteProduct ${id} failed, removing from local storage:`, err);
    }
    // Always remove from local storage to keep client clean
    const local = localStorage.getItem("products");
    if (local) {
        const products = JSON.parse(local);
        const filtered = products.filter((p: any) => p.id.toString() !== id.toString());
        localStorage.setItem("products", JSON.stringify(filtered));
    }
};