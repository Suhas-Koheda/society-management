import { Chip } from './ui/Chip';
import type { ComplaintPriority } from '../types';

const priorityColor: Record<ComplaintPriority, 'default' | 'warning' | 'error'> = {
  LOW: 'default',
  MEDIUM: 'warning',
  HIGH: 'error',
};

const priorityLabel: Record<ComplaintPriority, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};

export function ComplaintPriorityBadge({ priority }: { priority: ComplaintPriority }) {
  return (
    <Chip variant="status" color={priorityColor[priority]}>
      {priorityLabel[priority]}
    </Chip>
  );
}
