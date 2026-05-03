// frontend/src/pages/PublicProfilePage.tsx
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { usersApi } from '../api/users'
import Avatar from '../components/ui/Avatar'
import XPBar from '../components/ui/XPBar'
import StreakBadge from '../components/ui/StreakBadge'
import Spinner from '../components/ui/Spinner'
import { motion } from 'framer-motion'

export default function PublicProfilePage() {
  const { playerName } = useParams<{ playerName: string }>()

  const { data: profile, isLoading } = useQuery({
    queryKey: ['public-profile', playerName],
    queryFn: () => usersApi.getPublicProfile(playerName!).then((r) => r.data),
    enabled: !!playerName,
  })

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size={32} /></div>
  if (!profile) return <p className="text-center text-mist-dark py-20">User not found.</p>

  return (
    <div className="max-w-xl mx-auto space-y-6">
      {/* Profile header */}
      <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="card">
        <div className="flex items-start gap-5">
          <Avatar url={profile.avatar_url} name={profile.player_name} size={72} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-display text-2xl font-bold text-mist-light">{profile.player_name}</h1>
              <span className="badge-pill" style={{ background: 'rgba(107,63,160,0.2)', color: 'var(--color-arcane-glow)' }}>
                Lv.{profile.current_level} {profile.level_title}
              </span>
            </div>
            <p className="text-sm text-mist mt-0.5">{profile.full_name}</p>
            {profile.guild_names?.length > 0 && (
              <p className="text-xs text-mist-dark mt-1">
                🛡 {profile.guild_names.join(', ')}
              </p>
            )}
            <div className="mt-3 max-w-xs">
              <XPBar current={profile.total_xp} toNext={profile.xp_to_next_level} />
            </div>
            <div className="flex gap-4 mt-3">
              <StreakBadge type="daily" count={profile.daily_streak} />
              <StreakBadge type="weekly" count={profile.weekly_streak} />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Wall of Glory */}
      {profile.wall_of_glory?.length > 0 && (
        <div>
          <h2 className="font-display text-lg font-bold text-mist-light mb-3">⭐ Wall of Glory</h2>
          <div className="grid gap-3">
            {profile.wall_of_glory.map((w: any) => (
              <div key={w.completion_id} className="card flex items-center gap-3"
                style={{ border: '1px solid rgba(212,160,23,0.25)' }}>
                <span className="text-xl">{['🥇','🥈','🥉'][w.pin_order - 1]}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm text-mist-light truncate">{w.quest_title}</p>
                  <p className="text-xs text-mist-dark">+{w.points_earned} pts · +{w.xp_earned} XP</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Badges */}
      {profile.badges?.length > 0 && (
        <div>
          <h2 className="font-display text-lg font-bold text-mist-light mb-3">🏅 Badges</h2>
          <div className="grid grid-cols-4 gap-3">
            {profile.badges
              .filter((b: any) => b.is_unlocked)
              .map((b: any) => (
                <div key={b.badge_key} className="card text-center p-3"
                  style={{ border: '1px solid rgba(212,160,23,0.2)' }}
                  title={b.description}>
                  <div className="text-2xl mb-1">{b.icon_symbol}</div>
                  <p className="text-xs font-semibold text-mist-light truncate">{b.name}</p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
