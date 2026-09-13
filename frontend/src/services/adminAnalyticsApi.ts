import { api } from './api';
import {
  AdminOverviewAnalytics,
  AdminRiskAnalytics,
  AdminAcademicPerformanceAnalytics,
  AdminDepartmentAnalyticsResponse,
  AdminSemesterAnalyticsResponse,
  AdminInterventionsAnalytics,
} from '../types/adminAnalytics';

export const adminAnalyticsApi = {
  getOverview: async (params?: {
    department_id?: string;
    semester?: number;
  }): Promise<AdminOverviewAnalytics> => {
    const res = await api.get<AdminOverviewAnalytics>('/admin/analytics/overview', { params });
    return res.data;
  },

  getRisk: async (params?: {
    department_id?: string;
    semester?: number;
  }): Promise<AdminRiskAnalytics> => {
    const res = await api.get<AdminRiskAnalytics>('/admin/analytics/risk', { params });
    return res.data;
  },

  getPerformance: async (params?: {
    department_id?: string;
    semester?: number;
  }): Promise<AdminAcademicPerformanceAnalytics> => {
    const res = await api.get<AdminAcademicPerformanceAnalytics>('/admin/analytics/performance', {
      params,
    });
    return res.data;
  },

  getDepartments: async (): Promise<AdminDepartmentAnalyticsResponse> => {
    const res = await api.get<AdminDepartmentAnalyticsResponse>('/admin/analytics/departments');
    return res.data;
  },

  getSemesters: async (): Promise<AdminSemesterAnalyticsResponse> => {
    const res = await api.get<AdminSemesterAnalyticsResponse>('/admin/analytics/semesters');
    return res.data;
  },

  getInterventions: async (departmentId?: string): Promise<AdminInterventionsAnalytics> => {
    const res = await api.get<AdminInterventionsAnalytics>('/admin/analytics/interventions', {
      params: departmentId ? { department_id: departmentId } : undefined,
    });
    return res.data;
  },
};
