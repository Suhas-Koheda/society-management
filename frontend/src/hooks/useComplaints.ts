import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/complaints';

export function useMyComplaints() {
  return useQuery({
    queryKey: ['complaints'],
    queryFn: api.getMyComplaints,
  });
}

export function useMyComplaint(id: number) {
  return useQuery({
    queryKey: ['complaints', id],
    queryFn: () => api.getMyComplaint(id),
    enabled: !!id,
  });
}

export function useComplaintHistory(id: number) {
  return useQuery({
    queryKey: ['complaints', id, 'history'],
    queryFn: () => api.getComplaintHistory(id),
    enabled: !!id,
  });
}

export function useComplaintPhotos(id: number) {
  return useQuery({
    queryKey: ['complaints', id, 'photos'],
    queryFn: () => api.getComplaintPhotos(id),
    enabled: !!id,
  });
}

export function useCreateComplaint() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createComplaint,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['complaints'] }),
  });
}

export function useUploadPhoto(complaintId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => api.uploadComplaintPhoto(complaintId, file),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ['complaints', complaintId, 'photos'] }),
  });
}
