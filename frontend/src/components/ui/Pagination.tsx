import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  page: number;
  pages: number;
  total: number;
  limit: number;
  onPageChange: (newPage: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
  page,
  pages,
  total,
  limit,
  onPageChange
}) => {
  if (total === 0) return null;

  const start = (page - 1) * limit + 1;
  const end = Math.min(page * limit, total);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '1.25rem',
        padding: '0.5rem 0',
        color: 'var(--text-secondary)',
        fontSize: '0.875rem'
      }}
    >
      <div>
        Showing <strong style={{ color: 'var(--text-primary)' }}>{start}</strong> to <strong style={{ color: 'var(--text-primary)' }}>{end}</strong> of <strong style={{ color: 'var(--text-primary)' }}>{total}</strong> students
      </div>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <button
          className="btn btn-secondary btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={16} /> Previous
        </button>
        <span style={{ padding: '0 0.5rem', fontWeight: 600 }}>
          Page {page} of {Math.max(1, pages)}
        </span>
        <button
          className="btn btn-secondary btn-sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};
