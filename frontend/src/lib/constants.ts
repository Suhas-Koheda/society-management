import type {
  ComplaintCategory,
  ComplaintPriority,
  ComplaintStatus,
} from '../types';

export const ROUTES = {
  LOGIN: '/login',
  REGISTER: '/register',
  HOME: '/',
  COMPLAINTS: '/complaints',
  COMPLAINT_NEW: '/complaints/new',
  COMPLAINT_DETAIL: '/complaints/:id',
  NOTICES: '/notices',
  ADMIN: '/admin',
  ADMIN_COMPLAINTS: '/admin/complaints',
  ADMIN_COMPLAINT_DETAIL: '/admin/complaints/:id',
  ADMIN_NOTICES: '/admin/notices',
  ADMIN_NOTICE_NEW: '/admin/notices/new',
  ADMIN_NOTICE_EDIT: '/admin/notices/:id',
  ADMIN_SETTINGS: '/admin/settings',
} as const;

export const STATUS_COLORS: Record<ComplaintStatus, string> = {
  OPEN: 'var(--black)',
  IN_PROGRESS: 'var(--blue)',
  RESOLVED: 'var(--success)',
};

export const PRIORITY_COLORS: Record<ComplaintPriority, string> = {
  LOW: 'var(--content-secondary)',
  MEDIUM: 'var(--warning)',
  HIGH: 'var(--error)',
};

export const CATEGORY_LABELS: Record<ComplaintCategory, string> = {
  PLUMBING: 'Plumbing',
  ELECTRICAL: 'Electrical',
  CLEANING: 'Cleaning',
  SECURITY: 'Security',
  MAINTENANCE: 'Maintenance',
  OTHER: 'Other',
};

export const STATUS_LABELS: Record<ComplaintStatus, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
};

export const PRIORITY_LABELS: Record<ComplaintPriority, string> = {
  LOW: 'Low',
  MEDIUM: 'Medium',
  HIGH: 'High',
};
