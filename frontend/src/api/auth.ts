import { get, post } from './client';
import type { TokenResponse, UserResponse } from '../types';

export function register(data: {
  name: string;
  email: string;
  password: string;
}): Promise<UserResponse> {
  return post<UserResponse>('/auth/register', data);
}

export function login(data: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return post<TokenResponse>('/auth/login', data);
}

export function getMe(): Promise<UserResponse> {
  return get<UserResponse>('/auth/me');
}
