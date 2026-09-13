import React from 'react';
import { Bot, AlertTriangle, ShieldCheck } from 'lucide-react';
import type { ChatTurn } from '../../types';

interface ChatMessageBubbleProps {
  turn: ChatTurn;
  onSuggestionClick?: (prompt: string) => void;
}

/**
 * Renders **bold** emphasis as <strong> without a full markdown pipeline.
 * Everything else (bullets, line breaks) is preserved verbatim by pre-wrap CSS.
 */
const renderInline = (text: string): React.ReactNode[] =>
  text.split(/\*\*(.+?)\*\*/g).map((part, index) =>
    index % 2 === 1 ? (
      <strong key={`${index}-${part}`}>{part}</strong>
    ) : (
      <React.Fragment key={`${index}-${part}`}>{part}</React.Fragment>
    ),
  );

/**
 * Renders a single chat turn as a grounded-assistant bubble or a plain user
 * bubble. Assistant bubbles may carry intent, phase-level evidence citations,
 * source chips, suggested follow-ups, and the transparency disclaimer.
 */
export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({
  turn,
  onSuggestionClick,
}) => {
  if (turn.role === 'user') {
    return (
      <div className="chat-row chat-row--user">
        <div className="chat-bubble chat-bubble--user">{turn.content}</div>
      </div>
    );
  }

  const intent = turn.intent;
  const sources = turn.sourcesUsed ?? [];
  const evidence = turn.evidenceReferences ?? [];
  const followUps = turn.suggestedPrompts ?? [];

  return (
    <div className="chat-row chat-row--assistant">
      <div
        className="chat-avatar"
        aria-hidden="true"
      >
        <Bot size={16} />
      </div>
      <div
        className={`chat-bubble chat-bubble--assistant${turn.isError ? ' chat-bubble--error' : ''}`}
        role={turn.isError ? 'alert' : undefined}
      >
        {turn.isError && (
          <div className="chat-error-flag">
            <AlertTriangle size={13} /> COULD NOT GENERATE ANSWER
          </div>
        )}

        <div className="chat-bubble-text">{renderInline(turn.content)}</div>

        {intent && (
          <div className="chat-intent">
            <span className="mono-label">INTENT</span>
            <span className="node-status-chip">{intent.replace(/_/g, ' ')}</span>
          </div>
        )}

        {sources.length > 0 && (
          <div className="chat-sources">
            <span className="mono-label">GROUNDED IN</span>
            <div className="chat-source-chips">
              {sources.map((source) => (
                <span key={source} className="chat-source-chip">
                  {source}
                </span>
              ))}
            </div>
          </div>
        )}

        {evidence.length > 0 && (
          <details className="chat-evidence">
            <summary className="chat-evidence-summary">
              <ShieldCheck size={13} />
              <span className="mono-label">EVIDENCE REFERENCES ({evidence.length})</span>
            </summary>
            <ul className="chat-evidence-list">
              {evidence.map((ref) => (
                <li key={`${ref.phase}-${ref.title}`}>
                  <span className="chat-evidence-phase">PHASE {ref.phase}</span>
                  <span className="chat-evidence-title">{ref.title}</span>
                  <span className="chat-evidence-desc">{ref.description}</span>
                </li>
              ))}
            </ul>
          </details>
        )}

        {followUps.length > 0 && onSuggestionClick && (
          <div className="chat-followups">
            <span className="mono-label">FOLLOW-UP</span>
            <div className="chat-followup-chips">
              {followUps.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  className="chat-followup-chip"
                  onClick={() => onSuggestionClick(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {turn.disclaimer && (
          <p className="chat-disclaimer">{turn.disclaimer}</p>
        )}
      </div>
    </div>
  );
};