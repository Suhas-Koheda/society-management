import { Link } from 'react-router-dom';
import { useMyComplaints } from '../../hooks/useComplaints';
import { useNotices } from '../../hooks/useNotices';
import { StatsCard } from '../../components/StatsCard';
import { ComplaintStatusBadge } from '../../components/ComplaintStatusBadge';
import { Spinner } from '../../components/ui/Spinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { CATEGORY_LABELS } from '../../lib/constants';
import { formatRelativeTime } from '../../lib/formatters';

export function ResidentDashboard() {
  const { data, isLoading } = useMyComplaints();
  const { data: notices } = useNotices({ page: 1, page_size: 5 });

  if (isLoading) return <Spinner />;

  const items = data?.items || [];
  const open = items.filter((c) => c.status === 'OPEN').length;
  const inProgress = items.filter((c) => c.status === 'IN_PROGRESS').length;
  const resolved = items.filter((c) => c.status === 'RESOLVED').length;
  const importantNotices = notices?.items?.filter((n) => n.is_important) || [];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-4)' }}>
        <h2>MY DASHBOARD</h2>
        <Link to="/complaints/new" className="btn btn--primary btn--small">
          NEW COMPLAINT
        </Link>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--sp-3)', marginBottom: 'var(--sp-5)' }}>
        <StatsCard label="Total" value={data?.total || 0} />
        <StatsCard label="Open" value={open} />
        <StatsCard label="In Progress" value={inProgress} color="var(--blue)" />
        <StatsCard label="Resolved" value={resolved} color="var(--success)" />
      </div>

      {importantNotices.length > 0 && (
        <div style={{ marginBottom: 'var(--sp-5)' }}>
          <h3 style={{ marginBottom: 'var(--sp-2)', color: 'var(--error)' }}>IMPORTANT NOTICES</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
            {importantNotices.map((n) => (
              <Link
                key={n.id}
                to="/notices"
                style={{
                  display: 'block',
                  padding: 'var(--sp-3)',
                  border: '3px solid var(--error)',
                  textDecoration: 'none',
                  color: 'inherit',
                }}
              >
                <span style={{ fontWeight: 700, textTransform: 'uppercase', fontSize: '14px' }}>
                  {n.title}
                </span>
                <br />
                <span style={{ fontSize: '13px', color: 'var(--content-secondary)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {n.content}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      <h3 style={{ marginBottom: 'var(--sp-3)' }}>RECENT COMPLAINTS</h3>
      {items.length === 0 ? (
        <EmptyState message="No complaints yet. Create your first one." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {items.slice(0, 5).map((c) => (
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
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)', minWidth: '60px', textAlign: 'right' }}>
                {formatRelativeTime(c.created_at)}
              </span>
            </Link>
          ))}
          {items.length > 5 && (
            <Link to="/complaints" className="btn btn--ghost" style={{ alignSelf: 'center' }}>
              VIEW ALL {items.length} COMPLAINTS
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
