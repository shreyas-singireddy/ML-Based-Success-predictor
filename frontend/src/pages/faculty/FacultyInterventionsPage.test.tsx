import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { FacultyInterventionsPage } from './FacultyInterventionsPage';
import { Intervention, InterventionDashboardStats } from '../../types/intervention';
import { FacultyStudentSummary } from '../../types/faculty';

const mocks = vi.hoisted(() => ({
  listInterventions: vi.fn(),
  getDashboardStats: vi.fn(),
  createIntervention: vi.fn(),
  completeIntervention: vi.fn(),
  recordFollowUp: vi.fn(),
  recordOutcome: vi.fn(),
  getComparison: vi.fn(),
  getStudents: vi.fn(),
}));

vi.mock('../../services/interventionApi', () => ({
  interventionApi: {
    listInterventions: mocks.listInterventions,
    getDashboardStats: mocks.getDashboardStats,
    createIntervention: mocks.createIntervention,
    completeIntervention: mocks.completeIntervention,
    recordFollowUp: mocks.recordFollowUp,
    recordOutcome: mocks.recordOutcome,
    getComparison: mocks.getComparison,
  },
}));

vi.mock('../../services/facultyApi', () => ({
  facultyApi: {
    getStudents: mocks.getStudents,
  },
}));

const mockStats: InterventionDashboardStats = {
  total_interventions: 12,
  active_interventions: 5,
  follow_ups_due: 3,
  completed_interventions: 4,
  improved_count: 3,
  stable_count: 1,
  declined_count: 0,
  insufficient_data_count: 0,
};

const mockInterventions: Intervention[] = [
  {
    id: 'inv-1',
    student_id: 'stu-1',
    student_name: 'John Doe',
    student_number: 'STU-001',
    department_name: 'Computer Science',
    category: 'ATTENDANCE_SUPPORT',
    title: 'Attendance Mentoring Plan',
    description: 'Weekly check-in to monitor morning lecture attendance.',
    reason: 'Attendance declined from 85% to 70%',
    priority: 'HIGH',
    status: 'IN_PROGRESS',
    source: 'RISK_ALERT',
    baseline_risk_level: 'HIGH',
    baseline_predicted_cgpa: 6.8,
    baseline_attendance: 70.0,
    baseline_backlogs: 1,
    created_at: '2026-09-01T10:00:00Z',
    updated_at: '2026-09-01T10:00:00Z',
  },
  {
    id: 'inv-2',
    student_id: 'stu-2',
    student_name: 'Jane Smith',
    student_number: 'STU-002',
    department_name: 'Computer Science',
    category: 'EXAM_PREPARATION',
    title: 'Midterm Tutoring Support',
    description: 'Calculus and Discrete Math tutoring sessions.',
    priority: 'MEDIUM',
    status: 'COMPLETED',
    source: 'FACULTY_MANUAL',
    baseline_risk_level: 'MEDIUM',
    baseline_predicted_cgpa: 7.2,
    baseline_attendance: 82.0,
    baseline_backlogs: 0,
    created_at: '2026-08-15T10:00:00Z',
    updated_at: '2026-08-30T10:00:00Z',
    outcome: {
      id: 'out-1',
      intervention_id: 'inv-2',
      measured_at: '2026-09-10T10:00:00Z',
      previous_risk: 'MEDIUM',
      current_risk: 'LOW',
      previous_predicted_cgpa: 7.2,
      current_predicted_cgpa: 7.9,
      previous_attendance: 82.0,
      current_attendance: 88.0,
      previous_backlogs: 0,
      current_backlogs: 0,
      outcome_status: 'IMPROVED',
      notes: 'Strong improvements observed in exam series.',
      measured_by: 'user-1',
      created_at: '2026-09-10T10:00:00Z',
      updated_at: '2026-09-10T10:00:00Z',
    },
  },
];

const mockStudents: FacultyStudentSummary[] = [
  {
    id: 'stu-1',
    student_number: 'STU-001',
    name: 'John Doe',
    department_id: 'dept-1',
    department_name: 'Computer Science',
    current_semester: 4,
    gender: 'MALE',
    current_cgpa: 6.8,
    predicted_cgpa: 6.9,
    risk_level: 'HIGH',
    risk_score: 0.88,
    priority_score: 82.5,
    priority_tier: 'HIGH',
    attendance_percentage: 70.0,
    backlogs: 1,
    cgpa_trend: 'DECLINING',
    top_risk_factors: ['Attendance Deficit'],
    prediction_confidence: 0.85,
    confidence_category: 'HIGH',
    last_evaluated_at: '2026-09-01T10:00:00Z',
  },
];


describe('FacultyInterventionsPage (Phase 12)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listInterventions.mockResolvedValue({
      items: mockInterventions,
      total: mockInterventions.length,
      page: 1,
      page_size: 50,
      has_more: false,
    });
    mocks.getDashboardStats.mockResolvedValue(mockStats);
    mocks.getStudents.mockResolvedValue({
      items: mockStudents,
      total: 1,
      page: 1,
      page_size: 100,
      has_more: false,
    });
  });

  it('renders stats, header, and intervention cards correctly', async () => {
    render(
      <MemoryRouter>
        <FacultyInterventionsPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/LOADING INTERVENTION RECORDS/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Intervention Tracking & Outcome Management')).toBeInTheDocument();
      expect(screen.getByText('Attendance Mentoring Plan')).toBeInTheDocument();
      expect(screen.getByText('Midterm Tutoring Support')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });

    // Check stats
    expect(screen.getByText('12')).toBeInTheDocument(); // total
    expect(screen.getByText('5')).toBeInTheDocument(); // active
  });

  it('filters interventions when filter dropdown changes', async () => {
    render(
      <MemoryRouter>
        <FacultyInterventionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Attendance Mentoring Plan')).toBeInTheDocument();
    });

    const statusSelect = screen.getByDisplayValue('All Statuses');
    fireEvent.change(statusSelect, { target: { value: 'IN_PROGRESS' } });

    await waitFor(() => {
      expect(mocks.listInterventions).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'IN_PROGRESS' })
      );
    });
  });

  it('opens and submits new intervention modal', async () => {
    mocks.createIntervention.mockResolvedValue(mockInterventions[0]);

    render(
      <MemoryRouter>
        <FacultyInterventionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Intervention')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('New Intervention'));

    expect(screen.getByText('Create Academic Intervention')).toBeInTheDocument();

    // Select student
    const studentSelect = screen.getByRole('combobox', { name: /Select Target Student/i });
    fireEvent.change(studentSelect, { target: { value: 'stu-1' } });

    // Fill title and description
    const titleInput = screen.getByPlaceholderText(/e\.g\. Attendance & Mid-term Revision Mentoring/i);
    fireEvent.change(titleInput, { target: { value: 'Weekly Math Review' } });

    const descInput = screen.getByPlaceholderText(/Detail the agreed intervention steps/i);
    fireEvent.change(descInput, { target: { value: 'Review calculus module questions weekly.' } });

    // Submit
    const submitBtn = screen.getByRole('button', { name: /Record Intervention/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mocks.createIntervention).toHaveBeenCalledWith(
        expect.objectContaining({
          student_id: 'stu-1',
          title: 'Weekly Math Review',
          description: 'Review calculus module questions weekly.',
        })
      );
    });
  });

  it('renders observational disclaimer footer banner', async () => {
    render(
      <MemoryRouter>
        <FacultyInterventionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Observational Decision Support Disclaimer/i)).toBeInTheDocument();
      expect(screen.getByText(/The system does not assert deterministic causality/i)).toBeInTheDocument();
    });
  });
});
