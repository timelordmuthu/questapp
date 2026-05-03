// frontend/src/api/users.ts
import { apiClient } from './client'

export const usersApi = {
  getMe: () => apiClient.get('/users/me'),
  getPublicProfile: (playerName: string) => apiClient.get(`/users/${playerName}`),
  updateProfile: (data: { full_name?: string; timezone?: string }) =>
    apiClient.patch('/users/me', data),
  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post('/users/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient.post('/users/me/change-password', data),
  getQuestHistory: (params: {
    status?: string
    quest_type?: string
    category?: string
    page?: number
    page_size?: number
  }) => apiClient.get('/users/me/quest-history', { params }),
  pinQuest: (completion_id: string, pin_order: number) =>
    apiClient.post('/users/me/wall-of-glory/pin', { completion_id, pin_order }),
  unpinQuest: (completion_id: string) =>
    apiClient.delete(`/users/me/wall-of-glory/${completion_id}`),
}
