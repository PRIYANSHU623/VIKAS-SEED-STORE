import  api from  "./axios";

export const analyzeProduct = async( formData : FormData) => {
    const response = await api.post(
        "/scanner/analyze",
        formData,
        {
            headers: {
                "Content-Type" : "multipart/form-data"
            }
        }
    );
    return response.data;
}