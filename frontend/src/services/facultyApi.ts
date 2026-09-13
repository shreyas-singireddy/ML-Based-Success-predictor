import { api } from './api';
import {
  FacultyOverview,
  FacultyStudentListResponse,
  FacultyStudentDossier,
  FacultyAnalyticsResponse,
  FacultyAssistantChatResponse,
} from '../types/faculty';

export const facultyApi = {
  getOverview: async (departmentId?: string): Promise<FacultyOverview> => {
    const res = await api.get<FacultyOverview>('/faculty/overview', {
      params: departmentId ? { department_id: departmentId } : undefined,
    });
    return res.data;
  },

  getStudents: async (params: {
    search?: string;
    risk_level?: string;
    department_id?: string;
    semester?: number;
    min_attendance?: number;
    max_attendance?: number;
    min_cgpa?: number;
    max_cgpa?: number;
    has_backlogs?: boolean;
    sort_by?: string;
    page?: number;
    limit?: number;
  }): Promise<FacultyStudentListResponse> => {
    const res = await api.get<FacultyStudentListResponse>('/faculty/students', { params });
    return res.data;
  },

  getStudentDossier: async (studentId: string): Promise<FacultyStudentDossier> => {
    const res = await api.get<FacultyStudentDossier>(`/faculty/students/${studentId}`);
    return res.data;
  },

  getAnalytics: async (departmentId?: string): Promise<FacultyAnalyticsResponse> => {
    const res = await api.get<FacultyAnalyticsResponse>('/faculty/analytics', {
      params: departmentId ? { department_id: departmentId } : undefined,
    });
    return res.data;
  },

  askAssistant: async (message: string, studentId?: string): Promise<FacultyAssistantChatResponse> => {
    const res = await api.post<FacultyAssistantChatResponse>('/faculty/assistant/chat', {
      message,
      student_id: studentId || undefined,
    });
    return res.data;
  },

  getSuggestions: async (): Promise<string[]> => {
    const res = await api.get<{ suggestions: string[] }>('/faculty/assistant/suggestions');
    return res.data.suggestions;
  },
};
