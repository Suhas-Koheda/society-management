import { get, post, patch, del } from './client';
import type {
  DashboardResponse,
  AdminComplaintListResponse,
  AdminComplaintDetail,
  AdminComplaintHistoryItem,
  AdminComplaintPhotoResponse,
  ComplaintResponse,
  OverdueThresholdResponse,
  NoticeResponse,
  NoticeListResponse,
} from '../types';

export function getDashboard(): Promise<DashboardResponse> {
  return get<DashboardResponse>('/admin/dashboard');
}

export function getAdminComplaints(params?: {
  status?: string;
  category?: string;
  priority?: string;
  date_from?: string;
  date_to?: string;
  overdue?: boolean;
  page?: number;
  page_size?: number;
}): Promise<AdminComplaintListResponse> {
  const sp = new URLSearchParams();
  if (params?.status) sp.set('status', params.status);
  if (params?.category) sp.set('category', params.category);
  if (params?.priority) sp.set('priority', params.priority);
  if (params?.date_from) sp.set('date_from', params.date_from);
  if (params?.date_to) sp.set('date_to', params.date_to);
  if (params?.overdue !== undefined) sp.set('overdue', String(params.overdue));
  if (params?.page) sp.set('page', String(params.page));
  if (params?.page_size) sp.set('page_size', String(params.page_size));
  const qs = sp.toString();
  return get<AdminComplaintListResponse>(
    `/admin/complaints${qs ? `?${qs}` : ''}`,
  );
}

export function getAdminComplaint(
  id: number,
): Promise<AdminComplaintDetail> {
  return get<AdminComplaintDetail>(`/admin/complaints/${id}`);
}

export function updatePriority(
  id: number,
  priority: string,
): Promise<ComplaintResponse> {
  return patch<ComplaintResponse>(`/admin/complaints/${id}/priority`, {
    priority,
  });
}

export function updateStatus(
  id: number,
  status: string,
  note?: string,
): Promise<ComplaintResponse> {
  return patch<ComplaintResponse>(`/admin/complaints/${id}/status`, {
    status,
    note: note || null,
  });
}

export function getAdminComplaintHistory(
  id: number,
): Promise<AdminComplaintHistoryItem[]> {
  return get<AdminComplaintHistoryItem[]>(`/admin/complaints/${id}/history`);
}

export function getAdminComplaintPhotos(
  id: number,
): Promise<AdminComplaintPhotoResponse[]> {
  return get<AdminComplaintPhotoResponse[]>(
    `/admin/complaints/${id}/photos`,
  );
}

export function getOverdueThreshold(): Promise<OverdueThresholdResponse> {
  return get<OverdueThresholdResponse>('/admin/settings/overdue-threshold');
}

export function updateOverdueThreshold(
  days: number,
): Promise<OverdueThresholdResponse> {
  return patch<OverdueThresholdResponse>(
    '/admin/settings/overdue-threshold',
    { threshold_days: days },
  );
}

export function createNotice(data: {
  title: string;
  content: string;
  is_important: boolean;
}): Promise<NoticeResponse> {
  return post<NoticeResponse>('/admin/notices', data);
}

export function updateNotice(
  id: number,
  data: { title?: string; content?: string; is_important?: boolean },
): Promise<NoticeResponse> {
  return patch<NoticeResponse>(`/admin/notices/${id}`, data);
}

export function deleteNotice(id: number): Promise<void> {
  return del<void>(`/admin/notices/${id}`);
}

export function getAdminNotices(params?: {
  page?: number;
  page_size?: number;
}): Promise<NoticeListResponse> {
  const sp = new URLSearchParams();
  if (params?.page) sp.set('page', String(params.page));
  if (params?.page_size) sp.set('page_size', String(params.page_size));
  const qs = sp.toString();
  return get<NoticeListResponse>(`/admin/notices${qs ? `?${qs}` : ''}`);
}

export interface AdminUser {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at: string;
}

export function getUsers(): Promise<AdminUser[]> {
  return get<AdminUser[]>('/admin/users');
}

export function updateUserRole(
  userId: number,
  role: string,
): Promise<AdminUser> {
  return patch<AdminUser>(`/admin/users/${userId}/role`, { role });
}
