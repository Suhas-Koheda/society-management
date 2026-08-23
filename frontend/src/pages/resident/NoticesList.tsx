import { useState } from 'react';
import { useNotices } from '../../hooks/useNotices';
import { Card } from '../../components/ui/Card';
import { Spinner } from '../../components/ui/Spinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { formatDateTime } from '../../lib/formatters';

export function NoticesList() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useNotices({ page, page_size: 20 });

  if (isLoading) return <Spinner />;

  const items = data?.items || [];

  return (
    <div>
      <h2 style={{ marginBottom: 'var(--sp-4)' }}>NOTICES</h2>

      {items.length === 0 ? (
        <EmptyState message="No notices yet." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-3)' }}>
          {items.map((n) => (
            <Card key={n.id}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--sp-3)' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)', marginBottom: 'var(--sp-2)' }}>
                    <h4>{n.title}</h4>
                    {n.is_important && (
                      <span
                        style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: '10px',
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          letterSpacing: '1px',
                          padding: '2px 8px',
                          border: '2px solid var(--error)',
                          color: 'var(--error)',
                        }}
                      >
                        IMPORTANT
                      </span>
                    )}
                  </div>
                  <p style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{n.content}</p>
                  <div style={{ marginTop: 'var(--sp-2)', fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--content-secondary)' }}>
                    {formatDateTime(n.created_at)}
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
      )}
    </div>
  );
}
