import { useQuery } from '@tanstack/react-query';
import * as api from '../api/notices';

export function useNotices(params?: {
  important?: boolean;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: ['notices', params],
    queryFn: () => api.getNotices(params),
  });
}

export function useNotice(id: number) {
  return useQuery({
    queryKey: ['notices', id],
    queryFn: () => api.getNotice(id),
    enabled: !!id,
  });
}
