import { get } from './client';
import type { NoticeResponse, NoticeListResponse } from '../types';

export function getNotices(params?: {
  important?: boolean;
  page?: number;
  page_size?: number;
}): Promise<NoticeListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.important !== undefined)
    searchParams.set('important', String(params.important));
  if (params?.page) searchParams.set('page', String(params.page));
  if (params?.page_size)
    searchParams.set('page_size', String(params.page_size));
  const qs = searchParams.toString();
  return get<NoticeListResponse>(`/notices${qs ? `?${qs}` : ''}`);
}

export function getNotice(id: number): Promise<NoticeResponse> {
  return get<NoticeResponse>(`/notices/${id}`);
}
