import { useParams, Link } from 'react-router-dom';
import { useMyComplaint, useComplaintHistory, useComplaintPhotos } from '../../hooks/useComplaints';
import { ComplaintStatusBadge } from '../../components/ComplaintStatusBadge';
import { ComplaintPriorityBadge } from '../../components/ComplaintPriorityBadge';
import { PhotoUpload } from '../../components/PhotoUpload';
import { PhotoGrid } from '../../components/PhotoGrid';
import { Spinner } from '../../components/ui/Spinner';
import { CATEGORY_LABELS } from '../../lib/constants';
import { formatDateTime } from '../../lib/formatters';

export function ComplaintDetail() {
  const { id } = useParams<{ id: string }>();
  const complaintId = Number(id);
  const { data: complaint, isLoading: loadingComplaint } = useMyComplaint(complaintId);
  const { data: history } = useComplaintHistory(complaintId);
  const { data: photos } = useComplaintPhotos(complaintId);

  if (loadingComplaint) return <Spinner />;
  if (!complaint) return <div>Complaint not found.</div>;

  const isOpen = complaint.status !== 'RESOLVED';

  return (
    <div style={{ maxWidth: '800px' }}>
      <div style={{ marginBottom: 'var(--sp-3)' }}>
        <Link to="/complaints" className="btn btn--ghost" style={{ fontSize: '12px' }}>
          BACK TO COMPLAINTS
        </Link>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', marginBottom: 'var(--sp-4)' }}>
        <h2 style={{ flex: 1 }}>COMPLAINT #{complaint.id}</h2>
        <ComplaintStatusBadge status={complaint.status} />
        <ComplaintPriorityBadge priority={complaint.priority} />
      </div>

      <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ marginBottom: 'var(--sp-3)' }}>
          <span style={{ fontFamily: 'var(--font-headline)', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--content-secondary)' }}>
            CATEGORY
          </span>
          <div style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: '16px' }}>
            {CATEGORY_LABELS[complaint.category]}
          </div>
        </div>
        <div>
          <span style={{ fontFamily: 'var(--font-headline)', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--content-secondary)' }}>
            DESCRIPTION
          </span>
          <div style={{ marginTop: 'var(--sp-1)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {complaint.description}
          </div>
        </div>
        <div style={{ marginTop: 'var(--sp-3)', display: 'flex', gap: 'var(--sp-4)', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)' }}>
          <span>Created: {formatDateTime(complaint.created_at)}</span>
          {complaint.resolved_at && <span>Resolved: {formatDateTime(complaint.resolved_at)}</span>}
        </div>
      </div>

      <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--sp-3)' }}>
          <h3 style={{ fontSize: '16px' }}>PHOTOS</h3>
          {isOpen && <PhotoUpload complaintId={complaintId} />}
        </div>
        {photos && photos.length > 0 ? (
          <PhotoGrid photos={photos} />
        ) : (
          <div style={{
            border: '2px dashed var(--border-default)',
            padding: 'var(--sp-4)',
            textAlign: 'center',
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
            color: 'var(--content-tertiary)',
            textTransform: 'uppercase',
          }}>
            {isOpen ? 'No photos yet. Upload evidence of the issue.' : 'No photos were uploaded.'}
          </div>
        )}
      </div>

      <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
        <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>STATUS HISTORY</h3>
        {(!history || history.length === 0) ? (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-tertiary)', textTransform: 'uppercase' }}>
            No history
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {history.map((h, i) => (
              <div
                key={h.id}
                style={{
                  display: 'flex',
                  gap: 'var(--sp-3)',
                  padding: 'var(--sp-3) 0',
                  borderBottom: i < history.length - 1 ? '1px solid var(--black)' : 'none',
                }}
              >
                <div style={{ minWidth: '140px' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-secondary)' }}>
                    {formatDateTime(h.created_at)}
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <ComplaintStatusBadge status={h.status} />
                  {h.note && (
                    <div style={{ marginTop: 'var(--sp-1)', fontSize: '13px', color: 'var(--content-secondary)', fontStyle: 'italic' }}>
                      {h.note}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
