import { Chip } from './ui/Chip';
import type { ComplaintStatus } from '../types';

const statusColor: Record<ComplaintStatus, 'default' | 'success' | 'info' | 'warning' | 'error'> = {
  OPEN: 'default',
  IN_PROGRESS: 'info',
  RESOLVED: 'success',
};

const statusLabel: Record<ComplaintStatus, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
};

export function ComplaintStatusBadge({ status }: { status: ComplaintStatus }) {
  return (
    <Chip variant="status" color={statusColor[status]}>
      {statusLabel[status]}
    </Chip>
  );
}
