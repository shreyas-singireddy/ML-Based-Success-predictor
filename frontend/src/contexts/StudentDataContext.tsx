import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useAuth } from './AuthContext';
import { studentApi } from '../services/api';
import type { Student } from '../types';

interface StudentDataContextType {
  student: Student | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const StudentDataContext = createContext<StudentDataContextType | undefined>(undefined);

export const StudentDataProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [student, setStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!user?.profile_id) {
      setError('No associated student profile linked to your user account.');
      setLoading(false);
      setStudent(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await studentApi.getStudentById(user.profile_id);
      setStudent(data);
    } catch (err: any) {
      setError(
        err.response?.data?.error?.message ||
          'We could not load your academic record. Please try again.'
      );
      setStudent(null);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const value = useMemo(
    () => ({ student, loading, error, refresh }),
    [student, loading, error, refresh]
  );

  return <StudentDataContext.Provider value={value}>{children}</StudentDataContext.Provider>;
};

export const useStudentData = () => {
  const context = useContext(StudentDataContext);
  if (!context) {
    throw new Error('useStudentData must be used within a StudentDataProvider');
  }
  return context;
};