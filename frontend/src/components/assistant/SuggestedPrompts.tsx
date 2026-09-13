import React from 'react';
import { Sparkles } from 'lucide-react';
import type { AssistantSuggestion } from '../../types';

interface SuggestedPromptsProps {
  suggestions: AssistantSuggestion[];
  onSelect: (prompt: string) => void;
  disabled?: boolean;
}

/**
 * Personalized starter prompt chips shown in the empty chat state. Each prompt
 * maps to a grounded backend intent and is safe to send as-is.
 */
export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({
  suggestions,
  onSelect,
  disabled = false,
}) => {
  if (suggestions.length === 0) return null;

  return (
    <section className="suggested-prompts" aria-label="Suggested questions">
      <div className="suggested-prompts-head">
        <Sparkles size={14} />
        <span className="mono-label">TRY ASKING</span>
      </div>
      <div className="suggested-prompts-grid">
        {suggestions.map((suggestion) => (
          <button
            key={suggestion.prompt}
            type="button"
            className="suggested-prompt-chip"
            disabled={disabled}
            onClick={() => onSelect(suggestion.prompt)}
          >
            {suggestion.label}
          </button>
        ))}
      </div>
    </section>
  );
};