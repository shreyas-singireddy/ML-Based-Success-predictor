import { api } from './api';
import {
  Intervention,
  InterventionCreatePayload,
  InterventionDetail,
  InterventionListResponse,
  InterventionUpdatePayload,
  InterventionCompletePayload,
  InterventionFollowUpPayload,
  InterventionOutcomePayload,
  InterventionOutcome,
  BeforeAfterComparison,
  InterventionDashboardStats,
  InterventionStatus,
  InterventionCategory,
  InterventionPriority,
} from '../types/intervention';

export const interventionApi = {
  createIntervention: async (payload: InterventionCreatePayload): Promise<Intervention> => {
    const res = await api.post<Intervention>('/interventions', payload);
    return res.data;
  },

  listInterventions: async (params?: {
    student_id?: string;
    status?: InterventionStatus;
    category?: InterventionCategory;
    priority?: InterventionPriority;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<InterventionListResponse> => {
    const res = await api.get<InterventionListResponse>('/interventions', { params });
    return res.data;
  },

  getInterventionDetail: async (interventionId: string): Promise<InterventionDetail> => {
    const res = await api.get<InterventionDetail>(`/interventions/${interventionId}`);
    return res.data;
  },

  updateIntervention: async (
    interventionId: string,
    payload: InterventionUpdatePayload
  ): Promise<Intervention> => {
    const res = await api.patch<Intervention>(`/interventions/${interventionId}`, payload);
    return res.data;
  },

  completeIntervention: async (
    interventionId: string,
    payload: InterventionCompletePayload
  ): Promise<Intervention> => {
    const res = await api.post<Intervention>(`/interventions/${interventionId}/complete`, payload);
    return res.data;
  },

  recordFollowUp: async (
    interventionId: string,
    payload: InterventionFollowUpPayload
  ): Promise<Intervention> => {
    const res = await api.post<Intervention>(`/interventions/${interventionId}/follow-up`, payload);
    return res.data;
  },

  recordOutcome: async (
    interventionId: string,
    payload: InterventionOutcomePayload
  ): Promise<InterventionOutcome> => {
    const res = await api.post<InterventionOutcome>(`/interventions/${interventionId}/outcome`, payload);
    return res.data;
  },

  getComparison: async (interventionId: string): Promise<BeforeAfterComparison> => {
    const res = await api.get<BeforeAfterComparison>(`/interventions/${interventionId}/comparison`);
    return res.data;
  },

  getStudentInterventions: async (
    studentId: string,
    params?: { page?: number; page_size?: number }
  ): Promise<InterventionListResponse> => {
    const res = await api.get<InterventionListResponse>(`/students/${studentId}/interventions`, {
      params,
    });
    return res.data;
  },

  getDashboardStats: async (): Promise<InterventionDashboardStats> => {
    const res = await api.get<InterventionDashboardStats>('/interventions/dashboard-stats');
    return res.data;
  },
};
