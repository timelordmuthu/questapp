// frontend/src/components/quests/QuestCard.tsx
import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Clock, Zap, Star, CheckCircle, XCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { questsApi } from '../../api/quests'
import { useToast } from '../ui/Toast'
import Spinner from '../ui/Spinner'

interface QuestCardProps {
  quest: {
    instance_id: string
    template_id: string
    title: string
    quest_type: string
    category: string
    category_custom_label?: string
    source: string
    point_worth: number
    xp_worth: number
    period_end: string
    completion_status: string
    points_earned: number
    xp_earned: number
    group_total?: number
    group_done?: number
    is_competition: boolean
  }
}

const TYPE_LABELS: Record<string, string> = {
  daily: 'Daily',
  weekly: 'Weekly',
  occasional: 'Occasional',
  competition: 'Competition',
  group: 'Group',
}

function urgencyClass(deadline: Date): string {
  const hoursLeft = (deadline.getTime() - Date.now()) / 3_600_000
  if (hoursLeft < 2) return 'urgency-red'
  if (hoursLeft < 8) return 'urgency-yellow'
  return 'urgency-green'
}

export default function QuestCard({ quest }: QuestCardProps) {
  const { toast } = useToast()
  const qc = useQueryClient()
  const [justDone, setJustDone] = useState(false)

  const deadline = new Date(quest.period_end)
  const isDone = quest.completion_status === 'done'
  const isMissed = quest.completion_status === 'missed'

  const markDone = useMutation({
    mutationFn: () => questsApi.markDone(quest.instance_id),
    onSuccess: (res) => {
      const d = res.data
      setJustDone(true)
      toast(
        `+${d.points_earned} pts · +${d.xp_earned} XP${d.level_up ? ` · Level Up! → ${d.new_level}` : ''}${d.badges_earned?.length ? ` · Badge: ${d.badges_earned[0]}` : ''}`,
        'success'
      )
      qc.invalidateQueries({ queryKey: ['quest-feed'] })
      qc.invalidateQueries({ queryKey: ['me'] })
    },
    onError: (err: any) => {
      toast(err.response?.data?.detail ?? 'Failed to mark done.', 'error')
    },
  })

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="card card-hover relative overflow-hidden"
      style={{
        opacity: isMissed ? 0.6 : 1,
        border: isDone
          ? '1px solid rgba(34,197,94,0.3)'
          : isMissed
          ? '1px solid rgba(239,68,68,0.2)'
          : undefined,
      }}
    >
      {/* Glow accent for active quests */}
      {!isDone && !isMissed && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background: `linear-gradient(135deg, rgba(107,63,160,0.04) 0%, transparent 60%)`,
          }}
        />
      )}

      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`badge-pill type-${quest.quest_type}`}>
              {TYPE_LABELS[quest.quest_type] ?? quest.quest_type}
            </span>
            <span className="text-xs text-mist-dark">{quest.source}</span>
          </div>
          <h3 className="font-display text-base font-semibold text-mist-light leading-tight">
            {quest.title}
          </h3>
        </div>

        {/* Status icon */}
        {isDone && <CheckCircle size={20} style={{ color: 'var(--color-success)', flexShrink: 0 }} />}
        {isMissed && <XCircle size={20} style={{ color: 'var(--color-danger)', flexShrink: 0 }} />}
      </div>

      {/* Rewards row */}
      <div className="flex items-center gap-4 mb-3">
        <span className="flex items-center gap-1 text-sm font-semibold" style={{ color: 'var(--color-gold)' }}>
          <Star size={13} />
          {isDone ? quest.points_earned : quest.point_worth} pts
        </span>
        <span className="flex items-center gap-1 text-sm font-semibold" style={{ color: 'var(--color-arcane-glow)' }}>
          <Zap size={13} />
          {isDone ? quest.xp_earned : quest.xp_worth} XP
        </span>
        {/* Group progress */}
        {quest.quest_type === 'group' && quest.group_total != null && (
          <span className="text-xs text-mist-dark ml-auto">
            {quest.group_done}/{quest.group_total} done
          </span>
        )}
      </div>

      {/* Deadline row */}
      {!isDone && !isMissed && (
        <div className="flex items-center justify-between">
          <span className={`badge-pill ${urgencyClass(deadline)} flex items-center gap-1`}>
            <Clock size={11} />
            {formatDistanceToNow(deadline, { addSuffix: true })}
          </span>

          {!quest.is_competition && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              className="btn btn-primary text-xs py-1.5 px-3"
              onClick={() => markDone.mutate()}
              disabled={markDone.isPending}
            >
              {markDone.isPending ? <Spinner size={14} /> : 'Mark Done'}
            </motion.button>
          )}
        </div>
      )}

      {/* Success flash */}
      {justDone && (
        <motion.div
          initial={{ opacity: 1 }}
          animate={{ opacity: 0 }}
          transition={{ delay: 1.5, duration: 0.5 }}
          className="absolute inset-0 rounded-lg pointer-events-none"
          style={{ background: 'rgba(34,197,94,0.08)' }}
        />
      )}
    </motion.div>
  )
}
