import { api } from './api';
import type {
  CGPAPredictionRequest,
  CGPAPredictionResponse,
  CGPAExplainedResponse,
  RiskPredictionRequest,
  RiskPredictionResponse,
  RiskExplainedResponse,
  GlobalImportanceResponse,
} from '../types';

/**
 * Phase 3 / 4 / 5 — typed prediction clients.
 * The frontend ONLY consumes backend results. No ML logic lives here.
 */
export const predictionApi = {
  predictCgpa: async (payload: CGPAPredictionRequest): Promise<CGPAPredictionResponse> => {
    const res = await api.post<CGPAPredictionResponse>('/predictions/cgpa', payload);
    return res.data;
  },

  explainCgpa: async (payload: CGPAPredictionRequest): Promise<CGPAExplainedResponse> => {
    const res = await api.post<CGPAExplainedResponse>('/predictions/cgpa/explain', payload);
    return res.data;
  },

  predictRisk: async (payload: RiskPredictionRequest): Promise<RiskPredictionResponse> => {
    const res = await api.post<RiskPredictionResponse>('/predictions/risk', payload);
    return res.data;
  },

  explainRisk: async (payload: RiskPredictionRequest): Promise<RiskExplainedResponse> => {
    const res = await api.post<RiskExplainedResponse>('/predictions/risk/explain', payload);
    return res.data;
  },

  getCgpaImportance: async (): Promise<GlobalImportanceResponse> => {
    const res = await api.get<GlobalImportanceResponse>('/predictions/cgpa/importance');
    return res.data;
  },

  getRiskImportance: async (): Promise<GlobalImportanceResponse> => {
    const res = await api.get<GlobalImportanceResponse>('/predictions/risk/importance');
    return res.data;
  },
};