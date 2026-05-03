// frontend/src/api/quests.ts
import { apiClient } from './client'

export interface QuestCreatePayload {
  title: string
  description: string
  quest_type: string
  category: string
  category_custom_label?: string
  point_worth: number
  xp_worth: number
  start_at: string
  deadline_at?: string
  winner_point_reward?: number
  runner_up_point_reward?: number
  has_collective_deadline?: boolean
  collective_deadline_at?: string
  side_quest?: {
    title: string
    description: string
    point_worth: number
    xp_worth: number
    unlock_hour_offset: number
  }
  addon_quest?: {
    title: string
    description: string
    point_worth: number
    xp_worth: number
    addon_deadline: string
  }
}

export const questsApi = {
  getFeed: (params?: {
    quest_type?: string
    category?: string
    status?: string
    page?: number
    page_size?: number
  }) => apiClient.get('/quests/feed', { params }),

  markDone: (instanceId: string) =>
    apiClient.post(`/quests/${instanceId}/mark-done`),

  competitionVote: (
    instanceId: string,
    winner_id: string,
    runner_up_id?: string
  ) =>
    apiClient.post(`/quests/${instanceId}/competition-vote`, null, {
      params: { winner_id, runner_up_id },
    }),
}

// frontend/src/api/sanctum.ts
export const sanctumApi = {
  createQuest: (data: QuestCreatePayload) =>
    apiClient.post('/sanctum/quests', data),
  listQuests: () => apiClient.get('/sanctum/quests'),
  markDone: (instanceId: string) =>
    apiClient.post(`/sanctum/${instanceId}/mark-done`),
}

// frontend/src/api/guilds.ts
export const guildsApi = {
  create: (name: string) => apiClient.post('/guilds', { name }),
  join: (sigil_code: string) => apiClient.post('/guilds/join', { sigil_code }),
  get: (guildId: string) => apiClient.get(`/guilds/${guildId}`),
  update: (guildId: string, data: { name?: string; max_points_per_quest?: number; max_xp_per_quest?: number }) =>
    apiClient.patch(`/guilds/${guildId}`, data),
  leave: (guildId: string) => apiClient.post(`/guilds/${guildId}/leave`),
  removeMember: (guildId: string, userId: string) =>
    apiClient.delete(`/guilds/${guildId}/members/${userId}`),
  transferMaster: (guildId: string, new_gm_user_id: string) =>
    apiClient.post(`/guilds/${guildId}/transfer-master`, { new_gm_user_id }),
  regenerateSigil: (guildId: string) =>
    apiClient.post(`/guilds/${guildId}/regenerate-sigil`),
  dissolve: (guildId: string) => apiClient.delete(`/guilds/${guildId}`),

  // Proposals
  submitProposal: (guildId: string, data: QuestCreatePayload) =>
    apiClient.post(`/proposals/guilds/${guildId}/proposals`, data),
  listProposals: (guildId: string) =>
    apiClient.get(`/proposals/guilds/${guildId}/proposals`),
  voteProposal: (proposalId: string, vote: string, notes?: string) =>
    apiClient.post(`/proposals/proposals/${proposalId}/vote`, { vote, notes }),
}

// frontend/src/api/trades.ts
export const tradesApi = {
  validate: (data: { amount: number; guild_id: string }) =>
    apiClient.post('/trades/validate', data),
  send: (data: { receiver_player_name: string; amount: number; guild_id: string }) =>
    apiClient.post('/trades', data),
}

// frontend/src/api/notifications.ts
export const notificationsApi = {
  list: () => apiClient.get('/notifications'),
  unreadCount: () => apiClient.get('/notifications/unread-count'),
  markAllRead: () => apiClient.post('/notifications/mark-all-read'),
  markOneRead: (id: string) => apiClient.patch(`/notifications/${id}/read`),
  getSettings: () => apiClient.get('/notifications/settings'),
  updateSetting: (category: string, enabled: boolean) =>
    apiClient.patch('/notifications/settings', { category, enabled }),
}

// frontend/src/api/leaderboard.ts
export const leaderboardApi = {
  get: (guildId: string, type: 'all_time' | 'seasonal' = 'all_time') =>
    apiClient.get(`/leaderboard/guilds/${guildId}`, { params: { type } }),
}
