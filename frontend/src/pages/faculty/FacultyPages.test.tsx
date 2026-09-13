import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { FacultyOverviewPage } from './FacultyOverviewPage';
import { FacultyStudentsPage } from './FacultyStudentsPage';
import { FacultyStudentDetailPage } from './FacultyStudentDetailPage';
import { FacultyAnalyticsPage } from './FacultyAnalyticsPage';
import { FacultyAssistantPage } from './FacultyAssistantPage';
import { FacultyOverview, FacultyStudentListResponse, FacultyStudentDossier, FacultyAnalyticsResponse } from '../../types/faculty';

const mocks = vi.hoisted(() => ({
  getOverview: vi.fn(),
  getStudents: vi.fn(),
  getStudentDossier: vi.fn(),
  getAnalytics: vi.fn(),
  askAssistant: vi.fn(),
  getSuggestions: vi.fn(),
}));

vi.mock('../../services/facultyApi', () => ({
  facultyApi: {
    getOverview: mocks.getOverview,
    getStudents: mocks.getStudents,
    getStudentDossier: mocks.getStudentDossier,
    getAnalytics: mocks.getAnalytics,
    askAssistant: mocks.askAssistant,
    getSuggestions: mocks.getSuggestions,
  },
}));

const mockOverview: FacultyOverview = {
  students_monitored: 45,
  average_current_cgpa: 7.45,
  average_predicted_cgpa: 7.72,
  risk_distribution: { LOW: 25, MEDIUM: 12, HIGH: 6, CRITICAL: 2 },
  attendance_overview: {
    average_attendance: 81.5,
    below_75_count: 5,
    below_65_count: 2,
  },
  backlog_overview: {
    total_backlogs: 8,
    students_with_backlogs: 6,
    students_with_backlogs_pct: 13.3,
  },
  performance_categories: { EXCELLENT: 10, GOOD: 20, AVERAGE: 10, AT_RISK: 5 },
  top_risk_factors: [
    {
      factor_name: 'Attendance Deficit',
      feature_code: 'attendance_percentage',
      affected_students_count: 5,
      severity: 'HIGH',
      description: 'Attendance below 75% examination eligibility minimum.',
    },
  ],
  recent_alerts: [
    {
      id: 'ALERT_CRITICAL',
      alert_type: 'RISK_ELEVATED',
      severity: 'CRITICAL',
      title: 'Critical Risk Threshold Reached',
      description: '2 students exhibit severe multi-factor risk.',
      affected_count: 2,
      student_ids: ['STU-001', 'STU-002'],
      recommended_action: 'Initiate 1-on-1 counseling.',
    },
  ],
  department_scope: 'CSE',
  department_name: 'Computer Science & Engineering',
  last_analysis_timestamp: '2026-09-13T12:00:00Z',
};

const mockStudentsList: FacultyStudentListResponse = {
  items: [
    {
      id: 'stu-id-1',
      student_number: 'STU-2023-001',
      name: 'Alice Johnson',
      department_id: 'dept-1',
      department_code: 'CSE',
      department_name: 'Computer Science',
      current_semester: 4,
      gender: 'FEMALE',
      current_cgpa: 5.8,
      predicted_cgpa: 5.4,
      risk_level: 'CRITICAL',
      risk_score: 88.5,
      priority_score: 92.0,
      priority_tier: 'CRITICAL',
      attendance_percentage: 62.0,
      backlogs: 2,
      cgpa_trend: 'DECLINING',
      top_risk_factors: ['Attendance Deficit', 'Backlogs'],
      prediction_confidence: 0.85,
      confidence_category: 'HIGH',
      last_evaluated_at: '2026-09-13T12:00:00Z',
    },
    {
      id: 'stu-id-2',
      student_number: 'STU-2023-002',
      name: 'Bob Smith',
      department_id: 'dept-1',
      department_code: 'CSE',
      department_name: 'Computer Science',
      current_semester: 4,
      gender: 'MALE',
      current_cgpa: 8.2,
      predicted_cgpa: 8.4,
      risk_level: 'LOW',
      risk_score: 12.0,
      priority_score: 8.0,
      priority_tier: 'LOW',
      attendance_percentage: 92.0,
      backlogs: 0,
      cgpa_trend: 'IMPROVING',
      top_risk_factors: [],
      prediction_confidence: 0.92,
      confidence_category: 'HIGH',
      last_evaluated_at: '2026-09-13T12:00:00Z',
    },
  ],
  total: 2,
  page: 1,
  limit: 15,
  pages: 1,
  risk_counts: { ALL: 2, CRITICAL: 1, HIGH: 0, MEDIUM: 0, LOW: 1 },
};

const mockDossier: FacultyStudentDossier = {
  student: mockStudentsList.items[0],
  academic_history: [],
  trend_analysis: {
    semester_history: [
      { semester: 1, academic_year: '2023-2024', semester_cgpa: 6.8, attendance: 75, backlogs: 0 },
      { semester: 2, academic_year: '2023-2024', semester_cgpa: 6.2, attendance: 68, backlogs: 1 },
    ],
    current_cgpa: 5.8,
    predicted_cgpa: 5.4,
    trend_direction: 'DECLINING',
    delta_cgpa: -0.4,
    trend_description: 'Predicted semester CGPA indicates a notable decline from current standing.',
  },
  predicted_cgpa: 5.4,
  prediction_confidence: 0.85,
  risk_level: 'CRITICAL',
  risk_score: 88.5,
  faculty_explanation_summary: 'The risk model identifies attendance deficit and pending backlogs as the strongest contributing features.',
  grouped_recommendations: {
    immediate_attention: [
      {
        id: 'rec-1',
        title: 'Immediate Attendance Recovery',
        priority: 'CRITICAL',
        category: 'ATTENDANCE',
        evidence: [],
        action: 'Attend all remaining scheduled lecture hours.',
        expected_impact: 'HIGH',
        source: 'ACADEMIC_DATA',
        time_horizon: 'THIS_WEEK',
      },
    ],
    short_term: [],
    monitor: [],
  },
  model_version: 'cgpa_v1.0.0',
  risk_model_version: 'risk_v1.0.0',
  evaluated_at: '2026-09-13T12:00:00Z',
  disclaimer: 'Predictions and risk classifications are decision-support signals.',
};

const mockAnalytics: FacultyAnalyticsResponse = {
  department_scope: 'CSE',
  total_students: 45,
  risk_distribution: { LOW: 25, MEDIUM: 12, HIGH: 6, CRITICAL: 2 },
  performance_distribution: { EXCELLENT: 10, GOOD: 20, AVERAGE: 10, AT_RISK: 5 },
  cgpa_distribution: { '<6.0': 5, '6.0-7.0': 10, '7.0-8.0': 20, '8.0-9.0': 8, '>=9.0': 2 },
  attendance_distribution: { '<65%': 2, '65%-75%': 3, '75%-85%': 20, '>=85%': 20 },
  backlog_distribution: { '0': 39, '1-2': 4, '3-4': 2, '>=5': 0 },
  top_model_risk_factors: [
    {
      factor_name: 'Attendance Deficit',
      feature_code: 'attendance_percentage',
      affected_students_count: 5,
      severity: 'HIGH',
      description: 'Low attendance rate.',
    },
  ],
  semester_risk_hotspots: [
    {
      semester: 4,
      student_count: 22,
      high_critical_count: 6,
      high_critical_pct: 27.3,
      average_cgpa: 7.2,
      average_attendance: 79.5,
    },
  ],
  generated_at: '2026-09-13T12:00:00Z',
};

describe('Phase 10: Faculty Intelligence Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.getOverview.mockResolvedValue(mockOverview);
    mocks.getStudents.mockResolvedValue(mockStudentsList);
    mocks.getStudentDossier.mockResolvedValue(mockDossier);
    mocks.getAnalytics.mockResolvedValue(mockAnalytics);
    mocks.getSuggestions.mockResolvedValue(['Which students need attention?', 'Summarize risk factors']);
  });

  it('renders Faculty Overview KPIs, risk breakdown, and alerts', async () => {
    render(
      <MemoryRouter>
        <FacultyOverviewPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Faculty Intelligence Overview')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument(); // students monitored
    expect(screen.getByText('7.45')).toBeInTheDocument(); // avg current cgpa
    expect(screen.getByText('7.72')).toBeInTheDocument(); // avg predicted cgpa
    expect(screen.getByText('Critical Risk Threshold Reached')).toBeInTheDocument();
    expect(screen.getByText('Attendance Deficit')).toBeInTheDocument();
  });

  it('renders Faculty Priority Student Queue with filters', async () => {
    render(
      <MemoryRouter>
        <FacultyStudentsPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Academic Intervention Attention Queue')).toBeInTheDocument();
    expect(screen.getByText('Alice Johnson')).toBeInTheDocument();
    expect(screen.getByText('Bob Smith')).toBeInTheDocument();
    expect(screen.getByText(/STU-2023-001/i)).toBeInTheDocument();
    expect(screen.getByText(/CRITICAL \(92\)/i)).toBeInTheDocument();

  });

  it('renders comprehensive Student Intelligence Dossier', async () => {
    render(
      <MemoryRouter initialEntries={['/faculty/students/stu-id-1']}>
        <Routes>
          <Route path="/faculty/students/:studentId" element={<FacultyStudentDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    expect(await screen.findByText('Alice Johnson')).toBeInTheDocument();
    expect(screen.getByText('Academic Performance Trajectory')).toBeInTheDocument();
    expect(screen.getByText('Explainable AI Factor Analysis (Phase 5 SHAP)')).toBeInTheDocument();
    expect(screen.getByText('Immediate Attendance Recovery')).toBeInTheDocument();
    expect(screen.getByText('Faculty Intervention Decision Support')).toBeInTheDocument();
  });

  it('renders Faculty Class Analytics distributions and hotspots', async () => {
    render(
      <MemoryRouter>
        <FacultyAnalyticsPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Academic Performance & Risk Analytics')).toBeInTheDocument();
    expect(screen.getByText('CGPA Tier Distribution')).toBeInTheDocument();
    expect(screen.getByText('Attendance Rate Distribution')).toBeInTheDocument();
    expect(screen.getByText('Semester Academic Risk Hotspots')).toBeInTheDocument();
    expect(screen.getByText('Semester 4')).toBeInTheDocument();
  });

  it('renders Faculty GenAI Assistant and handles inquiry submission', async () => {
    mocks.askAssistant.mockResolvedValue({
      reply: 'There are 2 students in the critical risk tier requiring immediate advisement.',
      intent: 'FACULTY_ADVISORY',
      scope: 'Computer Science & Engineering',
      evidence_references: [{ source: 'Phase 4 Risk', label: 'Critical Count', value: '2' }],
      disclaimer: 'Decision-support only.',
    });

    render(
      <MemoryRouter>
        <FacultyAssistantPage />
      </MemoryRouter>
    );

    expect(await screen.findByText('Faculty AI Academic Advisor')).toBeInTheDocument();
    expect(screen.getByText('Which students need attention?')).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Ask about student group performance/i);
    fireEvent.change(input, { target: { value: 'Which students are high risk?' } });
    fireEvent.click(screen.getByRole('button', { name: /Ask/i }));

    expect(await screen.findByText(/There are 2 students in the critical risk tier/i)).toBeInTheDocument();
    expect(screen.getByText('Critical Count:')).toBeInTheDocument();
  });
});
