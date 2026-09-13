import { describe, expect, it, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AssistantPage } from './AssistantPage';
import type { Student } from '../../types';

const mocks = vi.hoisted(() => ({
  getSuggestions: vi.fn(),
  chat: vi.fn(),
  studentData: {
    student: null as Student | null,
    loading: false,
    error: null as string | null,
    refresh: vi.fn().mockResolvedValue(undefined),
  },
}));

vi.mock('../../services/assistantApi', () => ({
  assistantApi: {
    getSuggestions: mocks.getSuggestions,
    chat: mocks.chat,
  },
}));

vi.mock('../../contexts/StudentDataContext', () => ({
  useStudentData: () => mocks.studentData,
}));

const student: Student = {
  id: 'profile-1',
  student_number: 'STU-TEST-001',
  name: 'Student One',
  gender: 'FEMALE',
  age: 20,
  department_id: 'dept-1',
  department_code: 'CS',
  enrollment_year: 2023,
  current_semester: 3,
  cumulative_gpa: 8.5,
  total_credits_earned: 0,
  is_archived: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

describe('AssistantPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.studentData.student = student;
    mocks.studentData.loading = false;
    mocks.studentData.error = null;
    mocks.getSuggestions.mockResolvedValue({
      items: [
        { prompt: 'What is my predicted CGPA?', intent: 'PREDICTION', label: 'Check my CGPA' },
        { prompt: 'Why is my academic risk high?', intent: 'EXPLAINABILITY', label: 'Explain my risk' },
      ],
      generated_at: '2026-01-01T00:00:00Z',
    });
  });

  it('renders the welcome state with personalized starter prompts', async () => {
    render(<AssistantPage />);
    expect(await screen.findByText('Check my CGPA')).toBeInTheDocument();
    expect(screen.getByText('Explain my risk')).toBeInTheDocument();
    expect(screen.getByLabelText('Your question')).toBeInTheDocument();
  });

  it('sends a question and renders the grounded assistant answer', async () => {
    mocks.chat.mockResolvedValue({
      message: 'Your predicted CGPA is 8.10.',
      intent: 'PREDICTION',
      sources_used: ['Phase 2', 'Phase 3'],
      evidence_references: [
        { phase: 3, title: 'CGPA Prediction Engine', description: 'Predicted CGPA from the champion model.' },
      ],
      suggested_prompts: ['What is my academic risk?'],
      disclaimer: 'Decision-support only.',
      generated_at: '2026-01-01T00:00:00Z',
      status: 'success',
    });

    render(<AssistantPage />);

    const input = screen.getByLabelText('Your question');
    fireEvent.change(input, { target: { value: 'What is my predicted CGPA?' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    expect(await screen.findByText('Your predicted CGPA is 8.10.')).toBeInTheDocument();

    await waitFor(() => {
      expect(mocks.chat).toHaveBeenCalledTimes(1);
      expect(mocks.chat).toHaveBeenCalledWith(
        'What is my predicted CGPA?',
        expect.arrayContaining([expect.objectContaining({ role: 'user', content: 'What is my predicted CGPA?' })])
      );
    });
    expect(screen.getByText('Phase 3')).toBeInTheDocument();
  });

  it('renders an error bubble when the chat request fails', async () => {
    mocks.chat.mockRejectedValue({
      response: { data: { detail: 'The assistant engine is currently unavailable.' } },
    });

    render(<AssistantPage />);

    const input = screen.getByLabelText('Your question');
    fireEvent.change(input, { target: { value: 'What is my CGPA?' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send question' }));

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('The assistant engine is currently unavailable.');
  });

  it('shows the loading state while the student profile is loading', () => {
    mocks.studentData.loading = true;
    render(<AssistantPage />);
    expect(screen.getByText(/Connecting to your academic profile/i)).toBeInTheDocument();
  });

  it('shows an empty state when no student profile is linked', async () => {
    mocks.studentData.student = null;
    mocks.studentData.error = null;
    render(<AssistantPage />);
    expect(await screen.findByText('NO STUDENT PROFILE')).toBeInTheDocument();
  });
});