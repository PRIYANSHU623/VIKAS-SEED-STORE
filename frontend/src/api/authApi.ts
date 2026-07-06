import api from "./axios";

export const loginUser = async (data:any) => {
    const response = await api.post(
        "/auth/login",
        data
    );

    return response.data;
};

export const registerUSer = async (data: any) => {
    const response = await api.post(
        "/auth/register",
        data
    );
    return response.data;
};