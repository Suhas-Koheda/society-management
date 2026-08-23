import { get, post, uploadFile } from './client';
import type {
  ComplaintResponse,
  ComplaintListResponse,
  ComplaintHistoryResponse,
  ComplaintPhotoResponse,
} from '../types';

export function getMyComplaints(): Promise<ComplaintListResponse> {
  return get<ComplaintListResponse>('/complaints');
}

export function getMyComplaint(id: number): Promise<ComplaintResponse> {
  return get<ComplaintResponse>(`/complaints/${id}`);
}

export function createComplaint(data: {
  category: string;
  description: string;
}): Promise<ComplaintResponse> {
  return post<ComplaintResponse>('/complaints', data);
}

export function getComplaintHistory(
  id: number,
): Promise<ComplaintHistoryResponse[]> {
  return get<ComplaintHistoryResponse[]>(`/complaints/${id}/history`);
}

export function uploadComplaintPhoto(
  id: number,
  file: File,
): Promise<ComplaintPhotoResponse> {
  return uploadFile<ComplaintPhotoResponse>(`/complaints/${id}/photos`, file);
}

export function getComplaintPhotos(
  id: number,
): Promise<ComplaintPhotoResponse[]> {
  return get<ComplaintPhotoResponse[]>(`/complaints/${id}/photos`);
}
