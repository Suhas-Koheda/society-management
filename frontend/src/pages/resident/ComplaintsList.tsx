import { Link } from 'react-router-dom';
import { useMyComplaints } from '../../hooks/useComplaints';
import { ComplaintStatusBadge } from '../../components/ComplaintStatusBadge';
import { ComplaintPriorityBadge } from '../../components/ComplaintPriorityBadge';
import { Spinner } from '../../components/ui/Spinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { CATEGORY_LABELS } from '../../lib/constants';
import { formatDate } from '../../lib/formatters';

export function ComplaintsList() {
  const { data, isLoading } = useMyComplaints();

  if (isLoading) return <Spinner />;

  const items = data?.items || [];
  const open = items.filter((c) => c.status !== 'RESOLVED').length;
  const resolved = items.filter((c) => c.status === 'RESOLVED').length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-4)' }}>
        <div>
          <h2>MY COMPLAINTS</h2>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)', marginTop: 'var(--sp-1)' }}>
            {items.length} total -- {open} open, {resolved} resolved
          </p>
        </div>
        <Link to="/complaints/new" className="btn btn--primary btn--small">
          NEW COMPLAINT
        </Link>
      </div>

      {items.length === 0 ? (
        <EmptyState message="No complaints yet. Click NEW COMPLAINT to get started." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {items.map((c) => (
            <Link
              key={c.id}
              to={`/complaints/${c.id}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-3)',
                padding: 'var(--sp-3)',
                border: '3px solid var(--black)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)', minWidth: '40px' }}>
                #{c.id}
              </span>
              <span style={{ flex: 1 }}>
                <span style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: '14px' }}>
                  {CATEGORY_LABELS[c.category]}
                </span>
                <br />
                <span style={{ fontSize: '13px', color: 'var(--content-secondary)', display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {c.description}
                </span>
              </span>
              <ComplaintStatusBadge status={c.status} />
              <ComplaintPriorityBadge priority={c.priority} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)' }}>
                {formatDate(c.created_at)}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
