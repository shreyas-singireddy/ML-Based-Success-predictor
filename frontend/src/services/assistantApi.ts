import { api } from './api';
import type {
  ChatMessageInput,
  ChatResponse,
  SuggestionsResponse,
} from '../types';

/**
 * Phase 9 — GenAI Academic Assistant API client.
 *
 * The assistant is a grounded translation layer: every number in an answer is
 * drawn verbatim from verified Phase 2-8 engine output server-side. The
 * frontend only submits the student's question plus the short-lived,
 * client-held conversation history (never persisted).
 */
export const assistantApi = {
  /**
   * Send one authenticated chat turn and receive a fully grounded answer with
   * intent classification, phase-level evidence citations, and follow-ups.
   */
  chat: async (
    message: string,
    conversationHistory: ChatMessageInput[]
  ): Promise<ChatResponse> => {
    const res = await api.post<ChatResponse>('/assistant/chat', {
      message,
      conversation_history: conversationHistory,
    });
    return res.data;
  },

  /**
   * Fetch the personalized starter suggestions for the logged-in student.
   */
  getSuggestions: async (): Promise<SuggestionsResponse> => {
    const res = await api.get<SuggestionsResponse>('/assistant/suggestions');
    return res.data;
  },
};