// frontend/src/components/notifications/NotificationPanel.tsx
import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { formatDistanceToNow } from 'date-fns'
import { notificationsApi } from '../../api/quests'
import Spinner from '../ui/Spinner'

const CATEGORY_ICONS: Record<string, string> = {
  proposals_voting: '🗳',
  deadline_reminders: '⏰',
  level_badge: '⭐',
  trade_alerts: '💰',
  group_progress: '⚔',
  guild_membership: '🛡',
}

interface Props { onClose: () => void }

export default function NotificationPanel({ onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => notificationsApi.list().then((r) => r.data),
  })

  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['notif-unread'] })
    },
  })

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: -8, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8 }}
      className="absolute right-0 top-full mt-2 w-80 rounded-xl overflow-hidden z-50"
      style={{
        background: 'var(--color-void-100)',
        border: '1px solid var(--color-surface-border)',
        boxShadow: 'var(--shadow-card)',
      }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: '1px solid var(--color-surface-border)' }}>
        <span className="font-display text-sm font-semibold text-mist-light">Notifications</span>
        <button
          onClick={() => markAll.mutate()}
          className="text-xs text-arcane-light hover:text-arcane-glow transition-colors"
        >
          Mark all read
        </button>
      </div>

      {/* List */}
      <div className="overflow-y-auto max-h-96">
        {isLoading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : !data?.length ? (
          <p className="text-center text-sm text-mist-dark py-8">No notifications.</p>
        ) : (
          data.map((n: any) => (
            <div
              key={n.id}
              className="flex gap-3 px-4 py-3 transition-colors cursor-default"
              style={{
                background: n.is_read ? 'transparent' : 'rgba(107,63,160,0.06)',
                borderBottom: '1px solid var(--color-surface-border)',
              }}
            >
              <span className="text-lg flex-shrink-0 mt-0.5">
                {CATEGORY_ICONS[n.category] ?? '🔔'}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-mist-light">{n.title}</p>
                <p className="text-xs text-mist mt-0.5 leading-relaxed">{n.body}</p>
                <p className="text-xs text-mist-dark mt-1">
                  {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                </p>
              </div>
              {!n.is_read && (
                <div className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
                  style={{ background: 'var(--color-arcane-glow)' }} />
              )}
            </div>
          ))
        )}
      </div>
    </motion.div>
  )
}
