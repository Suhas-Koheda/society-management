import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  useAdminComplaint,
  useAdminComplaintHistory,
  useAdminComplaintPhotos,
  useUpdateStatus,
  useUpdatePriority,
} from '../../hooks/useAdmin';
import { ComplaintStatusBadge } from '../../components/ComplaintStatusBadge';
import { ComplaintPriorityBadge } from '../../components/ComplaintPriorityBadge';
import { PhotoGrid } from '../../components/PhotoGrid';
import { Spinner } from '../../components/ui/Spinner';
import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { useToast } from '../../components/ui/Toast';
import {
  CATEGORY_LABELS,
} from '../../lib/constants';
import { COMPLAINT_STATUSES, COMPLAINT_PRIORITIES } from '../../types';
import { formatDateTime } from '../../lib/formatters';

export function AdminComplaintDetail() {
  const { id } = useParams<{ id: string }>();
  const complaintId = Number(id);
  const { data: complaint, isLoading: loadingComplaint } = useAdminComplaint(complaintId);
  const { data: history } = useAdminComplaintHistory(complaintId);
  const { data: photos } = useAdminComplaintPhotos(complaintId);
  const updateStatus = useUpdateStatus();
  const updatePriority = useUpdatePriority();
  const { toast } = useToast();

  const [status, setStatus] = useState('');
  const [note, setNote] = useState('');
  const [priority, setPriority] = useState('');

  if (loadingComplaint) return <Spinner />;
  if (!complaint) return <div>Complaint not found.</div>;

  async function handleStatusUpdate() {
    if (!status) return;
    try {
      await updateStatus.mutateAsync({ id: complaintId, status, note: note || undefined });
      toast('Status updated', 'success');
      setStatus('');
      setNote('');
    } catch {
      toast('Failed to update status', 'error');
    }
  }

  async function handlePriorityUpdate() {
    if (!priority) return;
    try {
      await updatePriority.mutateAsync({ id: complaintId, priority });
      toast('Priority updated', 'success');
      setPriority('');
    } catch {
      toast('Failed to update priority', 'error');
    }
  }

  const validStatusTransitions: Record<string, string[]> = {
    OPEN: ['IN_PROGRESS'],
    IN_PROGRESS: ['RESOLVED'],
    RESOLVED: [],
  };
  const nextStatuses: string[] = validStatusTransitions[complaint.status] || [];
  const nextStatusOptions = COMPLAINT_STATUSES.filter((s) => nextStatuses.includes(s.value));

  return (
    <div style={{ maxWidth: '900px' }}>
      <div style={{ marginBottom: 'var(--sp-3)' }}>
        <Link to="/admin/complaints" className="btn btn--ghost" style={{ fontSize: '12px' }}>
          BACK TO COMPLAINTS
        </Link>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-3)', marginBottom: 'var(--sp-4)' }}>
        <h2 style={{ flex: 1 }}>COMPLAINT #{complaint.id}</h2>
        <ComplaintStatusBadge status={complaint.status} />
        <ComplaintPriorityBadge priority={complaint.priority} />
        {complaint.is_overdue && (
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '10px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', padding: '2px 8px', border: '2px solid var(--error)', color: 'var(--error)' }}>
            OVERDUE
          </span>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
          <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>DETAILS</h3>
          <div style={{ marginBottom: 'var(--sp-3)' }}>
            <span style={{ fontFamily: 'var(--font-headline)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--content-secondary)' }}>CATEGORY</span>
            <div style={{ fontWeight: 600, textTransform: 'uppercase' }}>{CATEGORY_LABELS[complaint.category]}</div>
          </div>
          <div style={{ marginBottom: 'var(--sp-3)' }}>
            <span style={{ fontFamily: 'var(--font-headline)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--content-secondary)' }}>DESCRIPTION</span>
            <div style={{ lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{complaint.description}</div>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--content-secondary)' }}>
            Created: {formatDateTime(complaint.created_at)}
            {complaint.resolved_at && <><br />Resolved: {formatDateTime(complaint.resolved_at)}</>}
          </div>
        </div>

        <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
          <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>RESIDENT</h3>
          <div style={{ marginBottom: 'var(--sp-3)' }}>
            <span style={{ fontFamily: 'var(--font-headline)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--content-secondary)' }}>NAME</span>
            <div style={{ fontWeight: 600 }}>{complaint.resident.name}</div>
          </div>
          <div>
            <span style={{ fontFamily: 'var(--font-headline)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '2px', color: 'var(--content-secondary)' }}>EMAIL</span>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px' }}>{complaint.resident.email}</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
          <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>UPDATE STATUS</h3>
          {nextStatusOptions.length > 0 ? (
            <>
              <Select
                label="New Status"
                options={nextStatusOptions}
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                placeholder={`Current: ${complaint.status.replace('_', ' ')}`}
              />
              <div style={{ marginTop: 'var(--sp-2)' }}>
                <Input
                  label="Admin Note (optional)"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Reason for change..."
                />
              </div>
              <div style={{ marginTop: 'var(--sp-3)' }}>
                <Button onClick={handleStatusUpdate} disabled={!status || updateStatus.isPending} fullWidth>
                  {updateStatus.isPending ? 'UPDATING...' : 'UPDATE STATUS'}
                </Button>
              </div>
            </>
          ) : (
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--content-secondary)', padding: 'var(--sp-3)', border: '2px dashed var(--border-default)' }}>
              {complaint.status === 'RESOLVED'
                ? 'This complaint is resolved and cannot be reopened.'
                : 'No valid transitions available.'}
            </div>
          )}
        </div>

        <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
          <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>UPDATE PRIORITY</h3>
          <Select
            label="New Priority"
            options={COMPLAINT_PRIORITIES}
            value={priority}
            onChange={(e) => setPriority(e.target.value)}
            placeholder={`Current: ${complaint.priority}`}
          />
          <div style={{ marginTop: 'var(--sp-3)' }}>
            <Button onClick={handlePriorityUpdate} disabled={!priority || updatePriority.isPending} fullWidth>
              {updatePriority.isPending ? 'UPDATING...' : 'UPDATE PRIORITY'}
            </Button>
          </div>
        </div>
      </div>

      <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
        <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>PHOTOS</h3>
        {photos && photos.length > 0 ? (
          <PhotoGrid photos={photos} />
        ) : (
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--content-tertiary)', textTransform: 'uppercase', padding: 'var(--sp-3)', border: '2px dashed var(--border-default)', textAlign: 'center' }}>
            No photos uploaded
          </div>
        )}
      </div>

      <div style={{ border: '3px solid var(--black)', padding: 'var(--sp-4)' }}>
        <h3 style={{ fontSize: '16px', marginBottom: 'var(--sp-3)' }}>HISTORY</h3>
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
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--sp-2)' }}>
                    <ComplaintStatusBadge status={h.status} />
                    <span style={{ fontSize: '13px', color: 'var(--content-secondary)' }}>
                      by {h.actor_name}
                    </span>
                  </div>
                  {h.note && (
                    <div style={{ marginTop: 'var(--sp-1)', fontSize: '13px', color: 'var(--content-secondary)', fontStyle: 'italic' }}>
                      "{h.note}"
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
