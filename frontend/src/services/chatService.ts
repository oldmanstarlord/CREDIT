import api from './api';

export interface ChatMessage {
  sender: 'user' | 'assistant';
  message: string;
  timestamp?: string;
}

export interface ChatResponse {
  response: string;
  confidence?: number;
  suggestions?: string[];
  application_id?: string | null;
  llm_provider?: string;
  llm_model?: string;
  fallback_used?: boolean;
  timestamp?: string;
}

export const chatService = {
  sendMessage: (applicationId: string | null, message: string) =>
    api.post<ChatResponse>('/chat/message', {
      message,
      application_id: applicationId || undefined,
    }),
};
