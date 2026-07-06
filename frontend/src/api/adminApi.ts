import api from "./axios";

export const getAdminAnalytics = async () => {
  const response = await api.get("/admin/analytics");
  return response.data;
};
