import { Link } from 'react-router-dom';
import { useDashboard } from '../../hooks/useAdmin';
import { StatsCard } from '../../components/StatsCard';
import { Spinner } from '../../components/ui/Spinner';
import { CATEGORY_LABELS, STATUS_LABELS } from '../../lib/constants';
import type { ComplaintStatus, ComplaintCategory } from '../../types';

export function AdminDashboard() {
  const { data, isLoading } = useDashboard();

  if (isLoading) return <Spinner />;
  if (!data) return null;

  return (
    <div>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>ADMIN DASHBOARD</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--sp-3)', marginBottom: 'var(--sp-5)' }}>
        <StatsCard label="Total" value={data.total_complaints} />
        <StatsCard label="Open" value={data.by_status.OPEN || 0} />
        <StatsCard label="In Progress" value={data.by_status.IN_PROGRESS || 0} color="var(--blue)" />
        <StatsCard label="Resolved" value={data.by_status.RESOLVED || 0} color="var(--success)" />
        <StatsCard label="Overdue" value={data.overdue_count} color="var(--error)" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-4)' }}>
        <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
          <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>BY STATUS</h3>
          {Object.entries(data.by_status).map(([status, count]) => (
            <Link
              key={status}
              to={`/admin/complaints?status=${status}`}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 'var(--sp-2) 0',
                borderBottom: '1px solid var(--black)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <span style={{ textTransform: 'uppercase', fontWeight: 600, fontSize: '14px' }}>
                {STATUS_LABELS[status as ComplaintStatus]}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700 }}>{count}</span>
            </Link>
          ))}
        </div>

        <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
          <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>BY CATEGORY</h3>
          {Object.entries(data.by_category).map(([cat, count]) => (
            <Link
              key={cat}
              to={`/admin/complaints?category=${cat}`}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 'var(--sp-2) 0',
                borderBottom: '1px solid var(--black)',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <span style={{ textTransform: 'uppercase', fontWeight: 600, fontSize: '14px' }}>
                {CATEGORY_LABELS[cat as ComplaintCategory]}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700 }}>{count}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
