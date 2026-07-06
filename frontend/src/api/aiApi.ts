import api from "./axios";

export interface ChatApiResponse {
  answer: string;
  response: string;
  tool_used?: string;
  tool_results?: {
    weather?: {
      success: boolean;
      data: any;
    };
    recommendation?: {
      success: boolean;
      data: {
        recommendations: any[];
        bundles: any[];
      };
    };
    product?: {
      success: boolean;
      data: {
        products: any[];
      };
    };
    order?: {
      success: boolean;
      data: {
        orders: any[];
      };
    };
  };
}

export const askAIChat = async (message: string, conversationId?: string): Promise<ChatApiResponse> => {
  const response = await api.post("/ai/chat", { 
    message,
    conversation_id: conversationId 
  });
  return response.data;
};
