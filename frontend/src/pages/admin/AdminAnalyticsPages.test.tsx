import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AdminOverviewPage } from './AdminOverviewPage';
import { AdminRiskPage } from './AdminRiskPage';
import { AdminPerformancePage } from './AdminPerformancePage';
import { AdminDepartmentsPage } from './AdminDepartmentsPage';
import { AdminSemestersPage } from './AdminSemestersPage';
import { AdminInterventionsPage } from './AdminInterventionsPage';
import {
  AdminOverviewAnalytics,
  AdminRiskAnalytics,
  AdminAcademicPerformanceAnalytics,
  AdminDepartmentAnalyticsResponse,
  AdminSemesterAnalyticsResponse,
  AdminInterventionsAnalytics,
} from '../../types/adminAnalytics';

const mocks = vi.hoisted(() => ({
  getOverview: vi.fn(),
  getRisk: vi.fn(),
  getPerformance: vi.fn(),
  getDepartments: vi.fn(),
  getSemesters: vi.fn(),
  getInterventions: vi.fn(),
}));

vi.mock('../../services/adminAnalyticsApi', () => ({
  adminAnalyticsApi: {
    getOverview: mocks.getOverview,
    getRisk: mocks.getRisk,
    getPerformance: mocks.getPerformance,
    getDepartments: mocks.getDepartments,
    getSemesters: mocks.getSemesters,
    getInterventions: mocks.getInterventions,
  },
}));

const mockOverviewData: AdminOverviewAnalytics = {
  total_students: 120,
  active_students: 120,
  students_monitored: 120,
  average_current_cgpa: 7.65,
  average_predicted_cgpa: 7.8,
  risk_distribution: { LOW: 70, MEDIUM: 30, HIGH: 15, CRITICAL: 5 },
  risk_percentages: { LOW: 58.3, MEDIUM: 25.0, HIGH: 12.5, CRITICAL: 4.2 },
  students_requiring_attention: 20,
  total_departments: 4,
  total_faculty: 18,
  total_interventions: 25,
  completed_interventions: 18,
  follow_ups_due: 4,
  total_alerts: 20,
};

const mockRiskData: AdminRiskAnalytics = {
  risk_distribution: { LOW: 70, MEDIUM: 30, HIGH: 15, CRITICAL: 5 },
  risk_percentages: { LOW: 58.3, MEDIUM: 25.0, HIGH: 12.5, CRITICAL: 4.2 },
  total_high_critical_count: 20,
  high_critical_percentage: 16.7,
  department_risk_breakdown: [
    {
      department_id: 'd-1',
      department_name: 'Computer Science',
      department_code: 'CSE',
      student_count: 50,
      risk_distribution: { LOW: 35, MEDIUM: 10, HIGH: 4, CRITICAL: 1 },
      high_or_critical_pct: 10.0,
    },
  ],
  semester_risk_breakdown: [
    {
      semester: 1,
      student_count: 30,
      risk_distribution: { LOW: 20, MEDIUM: 8, HIGH: 2, CRITICAL: 0 },
      average_cgpa: 7.8,
      average_attendance: 84.5,
    },
  ],
  attendance_vs_risk: [
    {
      attendance_bracket: '<65%',
      student_count: 8,
      risk_distribution: { LOW: 0, MEDIUM: 1, HIGH: 4, CRITICAL: 3 },
    },
  ],
};

const mockPerformanceData: AdminAcademicPerformanceAnalytics = {
  overall_cgpa_distribution: {
    '< 6.0': 8,
    '6.0 - 6.99': 22,
    '7.0 - 7.99': 45,
    '8.0 - 8.99': 35,
    '>= 9.0': 10,
  },
  average_current_cgpa: 7.65,
  average_predicted_cgpa: 7.8,
  average_attendance: 82.4,
  attendance_below_75_count: 14,
  attendance_below_65_count: 5,
  total_backlogs: 18,
  students_with_backlogs_count: 12,
  students_with_backlogs_pct: 10.0,
  department_performances: [
    {
      department_id: 'd-1',
      department_name: 'Computer Science',
      department_code: 'CSE',
      student_count: 50,
      average_current_cgpa: 7.85,
      average_predicted_cgpa: 7.95,
      average_attendance: 85.0,
      total_backlogs: 4,
      students_with_backlogs: 3,
      intervention_count: 10,
    },
  ],
};

const mockInterventionsData: AdminInterventionsAnalytics = {
  total_interventions: 25,
  by_status: { COMPLETED: 18, FOLLOW_UP_REQUIRED: 4, IN_PROGRESS: 3 },
  by_category: { ATTENDANCE_SUPPORT: 10, SUBJECT_SUPPORT: 8, STUDY_PLAN: 7 },
  by_priority: { HIGH: 10, MEDIUM: 12, LOW: 3 },
  completion_rate: 72.0,
  follow_ups_due_count: 4,
  outcome_distribution: { IMPROVED: 12, STABLE: 5, DECLINED: 1, INSUFFICIENT_DATA: 0 },
  measured_students_count: 18,
  improved_percentage_of_measured: 66.7,
  observational_statement:
    'Evaluation reflects observational changes in academic indicators following intervention records. No deterministic causal attribution is implied.',
};

describe('Phase 13 Admin Intelligence Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders AdminOverviewPage with KPIs and risk distributions', async () => {
    mocks.getOverview.mockResolvedValue(mockOverviewData);

    render(
      <MemoryRouter>
        <AdminOverviewPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/AGGREGATING INSTITUTION-WIDE ACADEMIC INTELLIGENCE/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Academic Intelligence & Institution Overview')).toBeInTheDocument();
      expect(screen.getByText('120')).toBeInTheDocument(); // total students
      expect(screen.getByText('7.65')).toBeInTheDocument(); // avg current cgpa
      expect(screen.getAllByText('20').length).toBeGreaterThanOrEqual(1);
    });

  });

  it('renders AdminRiskPage with department breakdown and attendance matrix', async () => {
    mocks.getRisk.mockResolvedValue(mockRiskData);

    render(
      <MemoryRouter>
        <AdminRiskPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System-Wide Risk Distribution & Factor Intelligence')).toBeInTheDocument();
      expect(screen.getByText(/20 Students in Elevated \/ Critical Risk Category/i)).toBeInTheDocument();
      expect(screen.getByText('Computer Science (CSE)')).toBeInTheDocument();
      expect(screen.getByText('<65%')).toBeInTheDocument();
    });
  });

  it('renders AdminPerformancePage with CGPA bands and department comparison', async () => {
    mocks.getPerformance.mockResolvedValue(mockPerformanceData);

    render(
      <MemoryRouter>
        <AdminPerformancePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Institutional Academic Performance')).toBeInTheDocument();
      expect(screen.getByText('Cumulative GPA Distribution Bands')).toBeInTheDocument();
      expect(screen.getByText('Computer Science (CSE)')).toBeInTheDocument();
    });
  });

  it('renders AdminDepartmentsPage with department cards', async () => {
    mocks.getDepartments.mockResolvedValue({
      departments: mockPerformanceData.department_performances,
      total_departments: 1,
    });

    render(
      <MemoryRouter>
        <AdminDepartmentsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Academic Department Comparative Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Computer Science')).toBeInTheDocument();
      expect(screen.getByText('CODE: CSE')).toBeInTheDocument();
    });
  });

  it('renders AdminSemestersPage with semester progression cards', async () => {
    mocks.getSemesters.mockResolvedValue({
      semesters: mockRiskData.semester_risk_breakdown,
      total_semesters: 1,
    });

    render(
      <MemoryRouter>
        <AdminSemestersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Semester Progression & Longitudinal Risk Trends')).toBeInTheDocument();
      expect(screen.getByText('Semester 1')).toBeInTheDocument();
      expect(screen.getByText('30 Students')).toBeInTheDocument();
    });
  });

  it('renders AdminInterventionsPage with observational outcome metrics and disclaimer', async () => {
    mocks.getInterventions.mockResolvedValue(mockInterventionsData);

    render(
      <MemoryRouter>
        <AdminInterventionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System-Wide Academic Interventions & Measured Outcomes')).toBeInTheDocument();
      expect(screen.getByText('72%')).toBeInTheDocument(); // completion rate
      expect(screen.getByText('66.7%')).toBeInTheDocument(); // improved %
      expect(screen.getByText(/No deterministic causal attribution is implied/i)).toBeInTheDocument();
    });
  });
});
