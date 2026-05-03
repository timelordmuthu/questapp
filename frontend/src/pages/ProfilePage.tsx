// frontend/src/pages/ProfilePage.tsx
import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Camera, Lock, Star, Clock, Pin } from 'lucide-react'
import { usersApi } from '../api/users'
import { useAuthStore } from '../store/authStore'
import { useToast } from '../components/ui/Toast'
import Avatar from '../components/ui/Avatar'
import XPBar from '../components/ui/XPBar'
import StreakBadge from '../components/ui/StreakBadge'
import Spinner from '../components/ui/Spinner'
import Modal from '../components/ui/Modal'
import { formatDistanceToNow } from 'date-fns'

const TIMEZONES = Intl.supportedValuesOf?.('timeZone') ?? ['UTC', 'Asia/Kolkata', 'America/New_York']

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore()
  const { toast } = useToast()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [showPwModal, setShowPwModal] = useState(false)
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '' })
  const [historyPage, setHistoryPage] = useState(1)
  const [activeTab, setActiveTab] = useState<'badges' | 'history' | 'wall'>('badges')

  const { data: profile, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => usersApi.getMe().then((r) => r.data),
  })

  const { data: history } = useQuery({
    queryKey: ['quest-history', historyPage],
    queryFn: () => usersApi.getQuestHistory({ page: historyPage, page_size: 15 }).then((r) => r.data),
    enabled: activeTab === 'history',
  })

  const uploadAvatar = useMutation({
    mutationFn: (file: File) => usersApi.uploadAvatar(file),
    onSuccess: (r) => {
      updateUser({ avatar_url: r.data.avatar_url })
      qc.invalidateQueries({ queryKey: ['me'] })
      toast('Avatar updated!', 'success')
    },
    onError: () => toast('Upload failed.', 'error'),
  })

  const updateProfile = useMutation({
    mutationFn: (data: { full_name?: string; timezone?: string }) => usersApi.updateProfile(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['me'] })
      toast('Profile updated.', 'success')
    },
  })

  const changePw = useMutation({
    mutationFn: () => usersApi.changePassword(pwForm),
    onSuccess: () => {
      toast('Password changed.', 'success')
      setShowPwModal(false)
      setPwForm({ current_password: '', new_password: '' })
    },
    onError: (err: any) => toast(err.response?.data?.detail ?? 'Failed.', 'error'),
  })

  const pinQuest = useMutation({
    mutationFn: ({ id, order }: { id: string; order: number }) => usersApi.pinQuest(id, order),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['me'] }); toast('Pinned to Wall of Glory!', 'success') },
    onError: (err: any) => toast(err.response?.data?.detail ?? 'Failed.', 'error'),
  })

  const unpinQuest = useMutation({
    mutationFn: (id: string) => usersApi.unpinQuest(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['me'] }); toast('Unpinned.', 'info') },
  })

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size={32} /></div>
  const me = profile ?? user
  if (!me) return null

  const TABS = [
    { id: 'badges' as const,  label: '🏅 Badges' },
    { id: 'history' as const, label: '📜 Quest History' },
    { id: 'wall' as const,    label: '⭐ Wall of Glory' },
  ]

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Profile card */}
      <div className="card">
        <div className="flex items-start gap-5">
          {/* Avatar with upload */}
          <div className="relative">
            <Avatar url={me.avatar_url} name={me.player_name} size={72} />
            <button
              onClick={() => fileRef.current?.click()}
              className="absolute -bottom-1 -right-1 p-1.5 rounded-full transition-colors"
              style={{ background: 'var(--color-arcane)', border: '2px solid var(--color-void)' }}
              title="Change avatar"
            >
              {uploadAvatar.isPending ? <Spinner size={12} /> : <Camera size={12} />}
            </button>
            <input ref={fileRef} type="file" accept="image/*" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadAvatar.mutate(f) }} />
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="font-display text-2xl font-bold text-mist-light">{me.player_name}</h1>
              <span className="badge-pill" style={{ background: 'rgba(107,63,160,0.2)', color: 'var(--color-arcane-glow)' }}>
                Lv.{me.current_level} {me.level_title}
              </span>
            </div>
            <p className="text-sm text-mist mt-0.5">{me.full_name}</p>
            <p className="text-xs text-mist-dark">{me.email}</p>

            <div className="mt-3 max-w-xs">
              <XPBar current={me.total_xp} toNext={me.xp_to_next_level} />
            </div>

            <div className="flex gap-4 mt-3">
              <StreakBadge type="daily" count={me.daily_streak} />
              <StreakBadge type="weekly" count={me.weekly_streak} />
              <span className="text-xs text-mist-dark flex items-center gap-1">
                <Star size={12} style={{ color: 'var(--color-gold)' }} />
                {me.total_points?.toLocaleString()} pts
              </span>
            </div>
          </div>
        </div>

        {/* Quick settings */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-5 pt-5"
          style={{ borderTop: '1px solid var(--color-surface-border)' }}>
          <div>
            <label className="block text-xs font-medium text-mist mb-1">Full Name</label>
            <input
              className="input"
              defaultValue={me.full_name}
              onBlur={(e) => {
                if (e.target.value !== me.full_name)
                  updateProfile.mutate({ full_name: e.target.value })
              }}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-mist mb-1">Timezone</label>
            <select
              className="input"
              defaultValue={me.timezone}
              onChange={(e) => updateProfile.mutate({ timezone: e.target.value })}
            >
              {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
            </select>
          </div>
        </div>

        <div className="flex justify-end mt-3">
          <button onClick={() => setShowPwModal(true)} className="btn btn-ghost text-xs gap-1.5">
            <Lock size={12} /> Change Password
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-lg" style={{ background: 'var(--color-surface)' }}>
        {TABS.map(({ id, label }) => (
          <button key={id} onClick={() => setActiveTab(id)}
            className="flex-1 py-2 rounded-md text-xs font-medium transition-all"
            style={{
              background: activeTab === id ? 'var(--color-arcane)' : 'transparent',
              color:      activeTab === id ? 'white'               : 'var(--color-mist-dark)',
            }}>
            {label}
          </button>
        ))}
      </div>

      {/* Badges tab */}
      {activeTab === 'badges' && (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
          {me.badges?.map((b: any) => (
            <motion.div
              key={b.badge_key}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="card text-center p-3"
              style={{
                opacity: b.is_unlocked ? 1 : 0.4,
                border: b.is_unlocked ? '1px solid rgba(212,160,23,0.3)' : undefined,
              }}
              title={b.is_unlocked ? b.description : `Hidden — ${b.hint}`}
            >
              <div className="text-2xl mb-1">{b.icon_symbol}</div>
              <p className="text-xs font-semibold text-mist-light truncate">{b.name}</p>
              {b.is_unlocked && b.earned_at && (
                <p className="text-xs text-mist-dark mt-0.5">
                  {new Date(b.earned_at).toLocaleDateString()}
                </p>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {/* History tab */}
      {activeTab === 'history' && (
        <div className="space-y-2">
          {history?.items?.map((item: any) => (
            <div key={item.completion_id} className="card flex items-center gap-3 py-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-mist-light truncate">{item.quest_title}</p>
                <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                  <span className={`badge-pill type-${item.quest_type} text-xs`}>{item.quest_type}</span>
                  <span className="text-xs text-mist-dark">{item.source}</span>
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-xs font-semibold" style={{ color: item.status === 'done' ? 'var(--color-success)' : 'var(--color-danger)' }}>
                  {item.status === 'done' ? `+${item.points_earned} pts` : 'Missed'}
                </p>
                {item.completed_at && (
                  <p className="text-xs text-mist-dark">{formatDistanceToNow(new Date(item.completed_at), { addSuffix: true })}</p>
                )}
              </div>
              {item.status === 'done' && !item.is_pinned && (
                <button
                  onClick={() => pinQuest.mutate({ id: item.completion_id, order: 1 })}
                  className="text-mist-dark hover:text-gold transition-colors"
                  title="Pin to Wall of Glory"
                >
                  <Pin size={14} />
                </button>
              )}
              {item.is_pinned && (
                <button
                  onClick={() => unpinQuest.mutate(item.completion_id)}
                  className="transition-colors"
                  style={{ color: 'var(--color-gold)' }}
                  title="Unpin"
                >
                  <Pin size={14} />
                </button>
              )}
            </div>
          ))}
          {(history?.total ?? 0) > 15 && (
            <div className="flex justify-center gap-3 pt-2">
              <button className="btn btn-ghost text-xs" disabled={historyPage === 1}
                onClick={() => setHistoryPage((p) => p - 1)}>← Previous</button>
              <button className="btn btn-ghost text-xs" disabled={(historyPage * 15) >= (history?.total ?? 0)}
                onClick={() => setHistoryPage((p) => p + 1)}>Next →</button>
            </div>
          )}
        </div>
      )}

      {/* Wall of Glory tab */}
      {activeTab === 'wall' && (
        <div>
          {!me.wall_of_glory?.length ? (
            <p className="text-center text-mist-dark py-12">
              Pin up to 3 completed quests from your history.
            </p>
          ) : (
            <div className="grid gap-3">
              {me.wall_of_glory.map((w: any) => (
                <div key={w.completion_id} className="card flex items-center gap-3"
                  style={{ border: '1px solid rgba(212,160,23,0.3)' }}>
                  <span className="text-2xl">{['🥇','🥈','🥉'][w.pin_order - 1]}</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-sm text-mist-light">{w.quest_title}</p>
                    <p className="text-xs text-mist-dark">+{w.points_earned} pts · +{w.xp_earned} XP</p>
                  </div>
                  <button onClick={() => unpinQuest.mutate(w.completion_id)}
                    className="text-mist-dark hover:text-danger transition-colors text-xs">
                    Unpin
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Change password modal */}
      <Modal open={showPwModal} onClose={() => setShowPwModal(false)} title="Change Password">
        <form onSubmit={(e) => { e.preventDefault(); changePw.mutate() }} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-mist mb-1">Current Password</label>
            <input type="password" className="input" value={pwForm.current_password}
              onChange={(e) => setPwForm((p) => ({ ...p, current_password: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-mist mb-1">New Password (min 8 chars)</label>
            <input type="password" className="input" value={pwForm.new_password}
              onChange={(e) => setPwForm((p) => ({ ...p, new_password: e.target.value }))} />
          </div>
          <button type="submit" className="btn btn-primary w-full" disabled={changePw.isPending}>
            {changePw.isPending ? <Spinner size={16} /> : 'Update Password'}
          </button>
        </form>
      </Modal>
    </div>
  )
}
