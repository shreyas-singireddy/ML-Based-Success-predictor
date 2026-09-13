import { describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { Skeleton } from './Skeleton';

describe('EmptyState', () => {
  it('renders the message and announces a status', () => {
    render(<EmptyState title="NO RECORDS" body="Nothing here yet." />);
    expect(screen.getByText('NO RECORDS')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders an optional action', () => {
    render(<EmptyState title="EMPTY" action={<button>Act</button>} />);
    expect(screen.getByRole('button', { name: 'Act' })).toBeInTheDocument();
  });
});

describe('ErrorState', () => {
  it('uses role=alert and surfaces the message', () => {
    render(<ErrorState title="LOAD FAILED" message="Network is down." />);
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('LOAD FAILED');
    expect(alert).toHaveTextContent('Network is down.');
  });

  it('triggers the retry handler', () => {
    const onRetry = vi.fn();
    render(<ErrorState title="LOAD FAILED" onRetry={onRetry} />);
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});

describe('Skeleton', () => {
  it('renders an accessible loading placeholder', () => {
    render(<Skeleton label="Loading chart" />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading chart');
  });
});