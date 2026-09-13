import { api } from './api';
import type {
  RecommendationRequest,
  RecommendationResponse,
} from '../types';

/**
 * Phase 8 — AI Personalized Recommendation Engine API Client.
 * All ranking, rule evaluations, SHAP contributions, and What-If outcomes
 * are generated deterministically by the backend.
 */
export const recommendationApi = {
  /**
   * Generate recommendations from explicit parameters or student_number.
   */
  generate: async (payload: RecommendationRequest): Promise<RecommendationResponse> => {
    const res = await api.post<RecommendationResponse>('/recommendations/generate', payload);
    return res.data;
  },

  /**
   * Get personalized recommendations for the currently authenticated student.
   */
  getMyRecommendations: async (): Promise<RecommendationResponse> => {
    const res = await api.get<RecommendationResponse>('/recommendations');
    return res.data;
  },
};
