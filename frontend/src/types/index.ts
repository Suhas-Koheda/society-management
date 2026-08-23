export type ComplaintStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED';
export type ComplaintPriority = 'LOW' | 'MEDIUM' | 'HIGH';
export type ComplaintCategory =
  | 'PLUMBING'
  | 'ELECTRICAL'
  | 'CLEANING'
  | 'SECURITY'
  | 'MAINTENANCE'
  | 'OTHER';

export interface UserResponse {
  id: number;
  name: string;
  email: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ComplaintResponse {
  id: number;
  resident_id: number;
  category: ComplaintCategory;
  description: string;
  status: ComplaintStatus;
  priority: ComplaintPriority;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface ComplaintListResponse {
  items: ComplaintResponse[];
  total: number;
}

export interface ComplaintHistoryResponse {
  id: number;
  status: ComplaintStatus;
  actor_id: number;
  note: string | null;
  created_at: string;
}

export interface ComplaintPhotoResponse {
  id: number;
  url: string;
  created_at: string;
}

export interface NoticeResponse {
  id: number;
  title: string;
  content: string;
  is_important: boolean;
  created_by: number;
  created_at: string;
  updated_at: string;
}

export interface NoticeListResponse {
  items: NoticeResponse[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AdminComplaintListItem {
  id: number;
  resident_id: number;
  category: ComplaintCategory;
  description: string;
  status: ComplaintStatus;
  priority: ComplaintPriority;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  is_overdue: boolean;
}

export interface AdminComplaintListResponse {
  items: AdminComplaintListItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ResidentBrief {
  id: number;
  name: string;
  email: string;
}

export interface AdminComplaintPhotoResponse {
  id: number;
  url: string;
  storage_key: string | null;
  created_at: string;
}

export interface AdminComplaintDetail extends AdminComplaintListItem {
  resident: ResidentBrief;
  photos: AdminComplaintPhotoResponse[];
}

export interface AdminComplaintHistoryItem {
  id: number;
  status: ComplaintStatus;
  actor_id: number;
  actor_name: string;
  actor_email: string;
  note: string | null;
  created_at: string;
}

export interface DashboardResponse {
  total_complaints: number;
  by_status: Record<ComplaintStatus, number>;
  by_category: Record<ComplaintCategory, number>;
  overdue_count: number;
}

export interface OverdueThresholdResponse {
  threshold_days: number;
}

export const COMPLAINT_CATEGORIES: { value: ComplaintCategory; label: string }[] = [
  { value: 'PLUMBING', label: 'Plumbing' },
  { value: 'ELECTRICAL', label: 'Electrical' },
  { value: 'CLEANING', label: 'Cleaning' },
  { value: 'SECURITY', label: 'Security' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'OTHER', label: 'Other' },
];

export const COMPLAINT_STATUSES: { value: ComplaintStatus; label: string }[] = [
  { value: 'OPEN', label: 'Open' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'RESOLVED', label: 'Resolved' },
];

export const COMPLAINT_PRIORITIES: { value: ComplaintPriority; label: string }[] = [
  { value: 'LOW', label: 'Low' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HIGH', label: 'High' },
];
