import api from './api';

export interface RegisterPayload {
  email: string;
  phone_number: string;
  password: string;
  full_name: string;
  date_of_birth?: string;
  aadhaar_number?: string;
  user_category?: string;
}

export interface LoginPayload {
  email?: string;
  phone_number?: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  phone_number: string;
  full_name: string;
  role?: string;
  date_of_birth?: string;
  gender?: string;
  aadhaar_number?: string;
  user_category?: string;
  is_verified: boolean;
  created_at: string;
}

export const authService = {
  register: (data: RegisterPayload) => api.post<TokenResponse>('/auth/register', data),
  login: (data: LoginPayload) => api.post<TokenResponse>('/auth/login', data),
  refresh: (refreshToken: string) => api.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get<UserProfile>('/auth/me'),
};
