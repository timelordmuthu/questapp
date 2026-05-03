// frontend/src/components/layout/RightSidebar.tsx
import { useQuery } from '@tanstack/react-query'
import { Trophy, Zap } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import { leaderboardApi } from '../../api/quests'
import Avatar from '../ui/Avatar'

export default function RightSidebar() {
  const { user } = useAuthStore()
  const { activeGuildId } = useUIStore()

  const { data: leaderboard } = useQuery({
    queryKey: ['leaderboard', activeGuildId, 'seasonal'],
    queryFn: () => leaderboardApi.get(activeGuildId!, 'seasonal').then((r) => r.data),
    enabled: !!activeGuildId,
  })

  return (
    <div
      className="h-full py-4 px-3 overflow-y-auto"
      style={{ background: 'var(--color-surface)', borderLeft: '1px solid var(--color-surface-border)' }}
    >
      {activeGuildId && leaderboard ? (
        <>
          <div className="flex items-center gap-2 mb-4">
            <Trophy size={14} style={{ color: 'var(--color-gold)' }} />
            <span className="text-xs font-semibold text-mist-dark uppercase tracking-wider">
              Season Rankings
            </span>
          </div>

          <div className="space-y-2">
            {leaderboard.entries.slice(0, 10).map((entry: any) => (
              <div
                key={entry.user_id}
                className="flex items-center gap-2 p-2 rounded-lg transition-colors"
                style={{
                  background: entry.is_current_user ? 'rgba(107,63,160,0.1)' : 'transparent',
                  border: entry.is_current_user ? '1px solid rgba(107,63,160,0.3)' : '1px solid transparent',
                }}
              >
                <span
                  className="text-xs font-bold w-5 text-center"
                  style={{
                    color: entry.rank === 1
                      ? 'var(--color-gold)'
                      : entry.rank === 2
                      ? 'var(--color-mist-light)'
                      : entry.rank === 3
                      ? 'var(--color-ember)'
                      : 'var(--color-mist-dark)',
                  }}
                >
                  {entry.rank}
                </span>
                <Avatar url={entry.avatar_url} name={entry.player_name} size={24} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-mist-light truncate">{entry.player_name}</p>
                </div>
                <span className="text-xs font-semibold" style={{ color: 'var(--color-gold)' }}>
                  {entry.points.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-center gap-3 opacity-50">
          <Zap size={28} style={{ color: 'var(--color-arcane)' }} />
          <p className="text-xs text-mist-dark">Select a Guild to see rankings</p>
        </div>
      )}
    </div>
  )
}
