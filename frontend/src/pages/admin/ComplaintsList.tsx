import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAdminComplaints } from '../../hooks/useAdmin';
import { ComplaintStatusBadge } from '../../components/ComplaintStatusBadge';
import { ComplaintPriorityBadge } from '../../components/ComplaintPriorityBadge';
import { FilterBar } from '../../components/FilterBar';
import { Spinner } from '../../components/ui/Spinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { CATEGORY_LABELS } from '../../lib/constants';
import { formatDate } from '../../lib/formatters';

export function AdminComplaintsList() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<{
    status?: string;
    category?: string;
    priority?: string;
    date_from?: string;
    date_to?: string;
    overdue?: boolean;
  }>({});

  const { data, isLoading } = useAdminComplaints({ ...filters, page, page_size: 20 });

  if (isLoading) return <Spinner />;

  const items = data?.items || [];

  return (
    <div>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>ALL COMPLAINTS</h2>

      <FilterBar filters={filters} onChange={(f) => { setFilters(f); setPage(1); }} />

      {items.length === 0 ? (
        <EmptyState message="No complaints match filters." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {items.map((c) => (
            <Link
              key={c.id}
              to={`/admin/complaints/${c.id}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-3)',
                padding: 'var(--sp-3)',
                border: `3px solid ${c.is_overdue ? 'var(--error)' : 'var(--black)'}`,
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
              {c.is_overdue && (
                <span style={{ fontFamily: 'var(--font-body)', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', padding: '2px 8px', border: '2px solid var(--error)', color: 'var(--error)' }}>
                  OVERDUE
                </span>
              )}
              <ComplaintStatusBadge status={c.status} />
              <ComplaintPriorityBadge priority={c.priority} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)' }}>
                {formatDate(c.created_at)}
              </span>
            </Link>
          ))}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
      )}
    </div>
  );
}
