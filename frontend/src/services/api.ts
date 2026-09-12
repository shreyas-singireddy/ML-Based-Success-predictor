import axios from 'axios';
import {
  Student,
  StudentListResponse,
  Department,
  SemesterAcademicRecord,
  CSVValidationPreview,
  CSVImportResult
} from '../types';

const API_BASE_URL = '/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor to handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const studentApi = {
  getStudents: async (params: {
    search?: string;
    department_id?: string;
    semester?: number;
    is_archived?: boolean;
    page?: number;
    limit?: number;
  }): Promise<StudentListResponse> => {
    const res = await api.get<StudentListResponse>('/students', { params });
    return res.data;
  },

  getStudentById: async (id: string): Promise<Student> => {
    const res = await api.get<Student>(`/students/${id}`);
    return res.data;
  },

  createStudent: async (studentData: any): Promise<Student> => {
    const res = await api.post<Student>('/students', studentData);
    return res.data;
  },

  updateStudent: async (id: string, updateData: any): Promise<Student> => {
    const res = await api.put<Student>(`/students/${id}`, updateData);
    return res.data;
  },

  archiveStudent: async (id: string): Promise<Student> => {
    const res = await api.delete<Student>(`/students/${id}`);
    return res.data;
  },

  restoreStudent: async (id: string): Promise<Student> => {
    const res = await api.post<Student>(`/students/${id}/restore`);
    return res.data;
  },

  getAcademicHistory: async (studentId: string): Promise<SemesterAcademicRecord[]> => {
    const res = await api.get<SemesterAcademicRecord[]>(`/students/${studentId}/academic-history`);
    return res.data;
  },

  addAcademicRecord: async (studentId: string, recordData: any): Promise<SemesterAcademicRecord> => {
    const res = await api.post<SemesterAcademicRecord>(`/students/${studentId}/academic-records`, recordData);
    return res.data;
  },

  updateAcademicRecord: async (studentId: string, recordId: string, recordData: any): Promise<SemesterAcademicRecord> => {
    const res = await api.put<SemesterAcademicRecord>(`/students/${studentId}/academic-records/${recordId}`, recordData);
    return res.data;
  },
};

export const departmentApi = {
  getDepartments: async (): Promise<Department[]> => {
    const res = await api.get<Department[]>('/departments');
    return res.data;
  },
};

export const csvApi = {
  validateCsv: async (file: File): Promise<CSVValidationPreview> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post<CSVValidationPreview>('/students/import/validate', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  confirmImport: async (token: string, duplicatePolicy: string): Promise<CSVImportResult> => {
    const res = await api.post<CSVImportResult>('/students/import/confirm', {
      import_batch_token: token,
      duplicate_policy: duplicatePolicy,
    });
    return res.data;
  },
};
