import './EmptyState.css';

interface EmptyStateProps {
  message?: string;
}

export function EmptyState({ message = 'Nothing here yet' }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <p className="empty-state__text">{message}</p>
    </div>
  );
}
