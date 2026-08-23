import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/admin';

export function useDashboard() {
  return useQuery({
    queryKey: ['admin', 'dashboard'],
    queryFn: api.getDashboard,
  });
}

export function useAdminComplaints(params?: {
  status?: string;
  category?: string;
  priority?: string;
  date_from?: string;
  date_to?: string;
  overdue?: boolean;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['admin', 'complaints', params],
    queryFn: () => api.getAdminComplaints(params),
  });
}

export function useAdminComplaint(id: number) {
  return useQuery({
    queryKey: ['admin', 'complaints', id],
    queryFn: () => api.getAdminComplaint(id),
    enabled: !!id,
  });
}

export function useAdminComplaintHistory(id: number) {
  return useQuery({
    queryKey: ['admin', 'complaints', id, 'history'],
    queryFn: () => api.getAdminComplaintHistory(id),
    enabled: !!id,
  });
}

export function useAdminComplaintPhotos(id: number) {
  return useQuery({
    queryKey: ['admin', 'complaints', id, 'photos'],
    queryFn: () => api.getAdminComplaintPhotos(id),
    enabled: !!id,
  });
}

export function useUpdatePriority() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, priority }: { id: number; priority: string }) =>
      api.updatePriority(id, priority),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['admin', 'complaints'] });
      qc.invalidateQueries({ queryKey: ['admin', 'complaints', vars.id] });
    },
  });
}

export function useUpdateStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      status,
      note,
    }: {
      id: number;
      status: string;
      note?: string;
    }) => api.updateStatus(id, status, note),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ['admin', 'complaints'] });
      qc.invalidateQueries({ queryKey: ['admin', 'complaints', vars.id] });
      qc.invalidateQueries({ queryKey: ['admin', 'dashboard'] });
    },
  });
}

export function useOverdueThreshold() {
  return useQuery({
    queryKey: ['admin', 'settings', 'overdue-threshold'],
    queryFn: api.getOverdueThreshold,
  });
}

export function useUpdateOverdueThreshold() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (days: number) => api.updateOverdueThreshold(days),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ['admin', 'settings', 'overdue-threshold'],
      }),
  });
}

export function useAdminNotices(params?: {
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['admin', 'notices', params],
    queryFn: () => api.getAdminNotices(params),
  });
}

export function useCreateNotice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createNotice,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'notices'] }),
  });
}

export function useUpdateNotice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: { title?: string; content?: string; is_important?: boolean };
    }) => api.updateNotice(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'notices'] }),
  });
}

export function useDeleteNotice() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteNotice(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'notices'] }),
  });
}

export function useUsers() {
  return useQuery({
    queryKey: ['admin', 'users'],
    queryFn: api.getUsers,
  });
}

export function useUpdateUserRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: string }) =>
      api.updateUserRole(userId, role),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'users'] }),
  });
}
