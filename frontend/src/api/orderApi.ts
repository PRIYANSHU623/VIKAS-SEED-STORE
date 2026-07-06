import api from "./axios";

export const getOrders = async () => {
    const response = await api.get("/orders/");
    return response.data;
};

export const getOrderById = async (id: string | number) => {
    const response = await api.get(`/orders/${id}`);
    return response.data;
};

export const createOrder = async (data: { product_id: number; quantity: number }) => {
    const response = await api.post("/orders/", data);
    return response.data;
};

export const updateOrder = async (id: string | number, data: { quantity?: number; status?: string }) => {
    const response = await api.put(`/orders/${id}`, data);
    return response.data;
};

export const deleteOrder = async (id: string | number) => {
    const response = await api.delete(`/orders/${id}`);
    return response.data;
};
