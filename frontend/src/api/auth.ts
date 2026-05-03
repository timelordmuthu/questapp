// frontend/src/api/auth.ts
import { apiClient } from './client'

export const authApi = {
  register: (data: {
    full_name: string
    player_name: string
    email: string
    password: string
    password_hint: string
    timezone: string
  }) => apiClient.post('/auth/register', data),

  login: (data: { player_name: string; password: string }) =>
    apiClient.post('/auth/login', data),

  logout: () => apiClient.post('/auth/logout'),

  forgotPassword: (email: string) =>
    apiClient.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, new_password: string) =>
    apiClient.post('/auth/reset-password', { token, new_password }),

  checkPlayerName: (player_name: string) =>
    apiClient.get(`/auth/check-player-name/${player_name}`),
}
