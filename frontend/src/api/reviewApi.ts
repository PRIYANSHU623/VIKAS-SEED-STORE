import api from "./axios";

export interface Review {
  id: number;
  product_id?: number | null;
  user_id?: number | null;
  user_name: string;
  rating: number;
  comment: string;
  created_at: string;
  updated_at: string;
  user_role?: string | null;
  user_location?: string | null;
  user_image?: string | null;
}

export const getHomepageReviews = async (): Promise<Review[]> => {
  const response = await api.get("/reviews/");
  return response.data;
};

export const getProductReviews = async (productId: string | number): Promise<Review[]> => {
  const response = await api.get(`/reviews/${productId}`);
  return response.data;
};

export const createReview = async (data: {
  product_id?: number | null;
  rating: number;
  comment: string;
  user_role?: string | null;
  user_location?: string | null;
  user_image?: string | null;
}): Promise<Review> => {
  const response = await api.post("/reviews/", data);
  return response.data;
};

export const updateReview = async (
  reviewId: number,
  data: { rating?: number; comment?: string }
): Promise<Review> => {
  const response = await api.put(`/reviews/${reviewId}`, data);
  return response.data;
};

export const deleteReview = async (reviewId: number): Promise<void> => {
  await api.delete(`/reviews/${reviewId}`);
};
