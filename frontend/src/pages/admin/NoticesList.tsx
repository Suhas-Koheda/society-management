import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAdminNotices, useDeleteNotice } from '../../hooks/useAdmin';
import { Spinner } from '../../components/ui/Spinner';
import { EmptyState } from '../../components/ui/EmptyState';
import { Pagination } from '../../components/ui/Pagination';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import { formatDateTime } from '../../lib/formatters';

export function AdminNoticesList() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useAdminNotices({ page, page_size: 20 });
  const deleteNotice = useDeleteNotice();
  const { toast } = useToast();
  const [deleteId, setDeleteId] = useState<number | null>(null);

  if (isLoading) return <Spinner />;

  const items = data?.items || [];

  async function handleDelete() {
    if (!deleteId) return;
    try {
      await deleteNotice.mutateAsync(deleteId);
      toast('Notice deleted', 'success');
      setDeleteId(null);
    } catch {
      toast('Failed to delete notice', 'error');
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-4)' }}>
        <h2>NOTICES</h2>
        <Link to="/admin/notices/new" className="btn btn--primary btn--small">
          NEW NOTICE
        </Link>
      </div>

      {items.length === 0 ? (
        <EmptyState message="No notices yet." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
          {items.map((n) => (
            <div
              key={n.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--sp-3)',
                padding: 'var(--sp-3)',
                border: `3px solid ${n.is_important ? 'var(--error)' : 'var(--black)'}`,
              }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)', minWidth: '40px' }}>
                #{n.id}
              </span>
              <span style={{ flex: 1 }}>
                <span style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: '14px' }}>
                  {n.title}
                </span>
                {n.is_important && (
                  <span style={{ marginLeft: 'var(--sp-2)', fontFamily: 'var(--font-body)', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', padding: '2px 8px', border: '2px solid var(--error)', color: 'var(--error)' }}>
                    IMPORTANT
                  </span>
                )}
                <br />
                <span style={{ fontSize: '13px', color: 'var(--content-secondary)' }}>
                  {formatDateTime(n.created_at)}
                </span>
              </span>
              <Link to={`/admin/notices/${n.id}`} className="btn btn--secondary btn--small">
                EDIT
              </Link>
              <Button variant="destructive" size="small" onClick={() => setDeleteId(n.id)}>
                DELETE
              </Button>
            </div>
          ))}
        </div>
      )}

      {data && data.total_pages > 1 && (
        <Pagination page={page} totalPages={data.total_pages} onPageChange={setPage} />
      )}

      <Modal open={deleteId !== null} onClose={() => setDeleteId(null)} title="DELETE NOTICE">
        <p style={{ marginBottom: 'var(--sp-4)' }}>Are you sure you want to delete this notice?</p>
        <div style={{ display: 'flex', gap: 'var(--sp-2)' }}>
          <Button variant="destructive" onClick={handleDelete} disabled={deleteNotice.isPending}>
            {deleteNotice.isPending ? 'DELETING...' : 'CONFIRM DELETE'}
          </Button>
          <Button variant="secondary" onClick={() => setDeleteId(null)}>
            CANCEL
          </Button>
        </div>
      </Modal>
    </div>
  );
}
