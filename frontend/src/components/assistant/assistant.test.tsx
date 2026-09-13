import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatMessageBubble } from './ChatMessageBubble';
import { SuggestedPrompts } from './SuggestedPrompts';
import type { ChatTurn, AssistantSuggestion, EvidenceSourceRef } from '../../types';

const evidence: EvidenceSourceRef[] = [
  { phase: 3, title: 'CGPA Prediction Engine', description: 'Predicted CGPA from the champion regression model.' },
  { phase: 4, title: 'Academic Risk Engine', description: 'Risk level with transparent 5-factor breakdown.' },
];

describe('ChatMessageBubble', () => {
  it('renders a right-aligned user turn verbatim', () => {
    render(
      <ChatMessageBubble
        turn={{
          id: 'u1',
          role: 'user',
          content: 'What is my predicted CGPA?',
          timestamp: '2026-01-01T00:00:00Z',
        }}
      />
    );
    expect(screen.getByText('What is my predicted CGPA?')).toBeInTheDocument();
  });

  it('renders an assistant turn with intent, sources, and evidence references', () => {
    const turn: ChatTurn = {
      id: 'a1',
      role: 'assistant',
      content: 'Your predicted CGPA is 8.10.',
      timestamp: '2026-01-01T00:00:00Z',
      intent: 'PREDICTION',
      sourcesUsed: ['Phase 2', 'Phase 3'],
      evidenceReferences: evidence,
    };
    render(<ChatMessageBubble turn={turn} />);
    expect(screen.getByText('Your predicted CGPA is 8.10.')).toBeInTheDocument();
    expect(screen.getByText('PREDICTION')).toBeInTheDocument();
    expect(screen.getByText('Phase 2')).toBeInTheDocument();
    expect(screen.getByText('Phase 3')).toBeInTheDocument();
    expect(screen.getByText('CGPA Prediction Engine')).toBeInTheDocument();
    expect(screen.getByText('Academic Risk Engine')).toBeInTheDocument();
  });

  it('renders follow-up chips and calls the click handler', () => {
    const onSuggestionClick = vi.fn();
    render(
      <ChatMessageBubble
        turn={{
          id: 'a2',
          role: 'assistant',
          content: 'Here is your answer.',
          timestamp: '2026-01-01T00:00:00Z',
          suggestedPrompts: ['What is my academic risk?', 'Explain why my score is low.'],
        }}
        onSuggestionClick={onSuggestionClick}
      />
    );
    const chip = screen.getByRole('button', { name: 'What is my academic risk?' });
    fireEvent.click(chip);
    expect(onSuggestionClick).toHaveBeenCalledWith('What is my academic risk?');
  });

  it('flags error turns with role=alert', () => {
    render(
      <ChatMessageBubble
        turn={{
          id: 'a3',
          role: 'assistant',
          content: 'The assistant is unavailable right now.',
          timestamp: '2026-01-01T00:00:00Z',
          isError: true,
        }}
      />
    );
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('The assistant is unavailable right now.');
  });
});

describe('SuggestedPrompts', () => {
  const suggestions: AssistantSuggestion[] = [
    { prompt: 'What is my predicted CGPA?', intent: 'PREDICTION', label: 'Check my CGPA' },
    { prompt: 'Why is my academic risk high?', intent: 'EXPLAINABILITY', label: 'Explain my risk' },
  ];

  it('renders labels and triggers select', () => {
    const onSelect = vi.fn();
    render(<SuggestedPrompts suggestions={suggestions} onSelect={onSelect} />);
    expect(screen.getByText('Check my CGPA')).toBeInTheDocument();
    expect(screen.getByText('Explain my risk')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Explain my risk' }));
    expect(onSelect).toHaveBeenCalledWith('Why is my academic risk high?');
  });

  it('renders nothing for an empty suggestion list', () => {
    const { container } = render(<SuggestedPrompts suggestions={[]} onSelect={() => {}} />);
    expect(container.firstChild).toBeNull();
  });

  it('respects the disabled prop', () => {
    render(<SuggestedPrompts suggestions={suggestions} onSelect={() => {}} disabled />);
    expect(screen.getByRole('button', { name: 'Check my CGPA' })).toBeDisabled();
  });
});