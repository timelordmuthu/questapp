// frontend/src/components/quests/QuestCreateForm.tsx
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useToast } from '../ui/Toast'
import Spinner from '../ui/Spinner'
import type { QuestCreatePayload } from '../../api/quests'

interface Props {
  mode: 'sanctum' | 'guild'
  guildId?: string
  onSuccess: () => void
  submitFn: (data: QuestCreatePayload) => Promise<any>
}

const QUEST_TYPES = ['daily', 'weekly', 'occasional', 'competition', 'group']
const CATEGORIES  = ['fitness', 'study', 'creative', 'social', 'wellness', 'other']

export default function QuestCreateForm({ mode, guildId, onSuccess, submitFn }: Props) {
  const { toast } = useToast()
  const qc = useQueryClient()

  const [form, setForm] = useState<Partial<QuestCreatePayload>>({
    quest_type: 'daily',
    category: 'fitness',
    point_worth: 100,
    xp_worth: 50,
    has_collective_deadline: false,
    start_at: new Date().toISOString().slice(0, 16),
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const set = (key: keyof QuestCreatePayload, value: any) =>
    setForm((p) => ({ ...p, [key]: value }))

  const validate = (): boolean => {
    const errs: Record<string, string> = {}
    if (!form.title?.trim()) errs.title = 'Title is required.'
    if (!form.description?.trim()) errs.description = 'Description is required.'
    if (!form.point_worth || form.point_worth < 1) errs.point_worth = 'Must be ≥ 1.'
    if (!form.xp_worth    || form.xp_worth    < 1) errs.xp_worth    = 'Must be ≥ 1.'
    if (!form.start_at) errs.start_at = 'Start time required.'
    if (form.quest_type === 'competition' && !form.winner_point_reward)
      errs.winner_point_reward = 'Winner reward required for Competition quests.'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const mutation = useMutation({
    mutationFn: () => {
      const payload: QuestCreatePayload = {
        title:                  form.title!,
        description:            form.description!,
        quest_type:             form.quest_type!,
        category:               form.category!,
        category_custom_label:  form.category_custom_label,
        point_worth:            form.point_worth!,
        xp_worth:               form.xp_worth!,
        start_at:               new Date(form.start_at!).toISOString(),
        deadline_at:            form.deadline_at ? new Date(form.deadline_at).toISOString() : undefined,
        winner_point_reward:    form.winner_point_reward,
        runner_up_point_reward: form.runner_up_point_reward,
        has_collective_deadline:form.has_collective_deadline,
        collective_deadline_at: form.collective_deadline_at ? new Date(form.collective_deadline_at).toISOString() : undefined,
        side_quest:             form.side_quest,
        addon_quest:            form.addon_quest,
      }
      return submitFn(payload)
    },
    onSuccess: () => {
      toast(mode === 'sanctum' ? 'Quest created!' : 'Proposal submitted!', 'success')
      qc.invalidateQueries({ queryKey: ['quest-feed'] })
      qc.invalidateQueries({ queryKey: ['proposals'] })
      onSuccess()
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail
      toast(Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : detail ?? 'Failed.', 'error')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) mutation.mutate()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Title */}
      <div>
        <label className="block text-xs font-medium text-mist mb-1">Quest Title *</label>
        <input className={`input ${errors.title ? 'error' : ''}`} placeholder="E.g. Morning Run"
          value={form.title ?? ''} onChange={(e) => set('title', e.target.value)} />
        {errors.title && <p className="text-xs text-danger mt-1">{errors.title}</p>}
      </div>

      {/* Description */}
      <div>
        <label className="block text-xs font-medium text-mist mb-1">Description *</label>
        <textarea className={`input resize-none ${errors.description ? 'error' : ''}`} rows={3}
          placeholder="What does completing this quest entail?"
          value={form.description ?? ''} onChange={(e) => set('description', e.target.value)} />
        {errors.description && <p className="text-xs text-danger mt-1">{errors.description}</p>}
      </div>

      {/* Type + Category row */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Quest Type *</label>
          <select className="input" value={form.quest_type} onChange={(e) => set('quest_type', e.target.value)}>
            {QUEST_TYPES.map((t) => (
              <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Category *</label>
          <select className="input" value={form.category} onChange={(e) => set('category', e.target.value)}>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Custom category label */}
      {form.category === 'other' && (
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Custom Category Label (max 30 chars)</label>
          <input className="input" maxLength={30} placeholder="E.g. Language Learning"
            value={form.category_custom_label ?? ''} onChange={(e) => set('category_custom_label', e.target.value)} />
        </div>
      )}

      {/* Points + XP row */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Points *</label>
          <input type="number" className={`input ${errors.point_worth ? 'error' : ''}`} min={1}
            value={form.point_worth ?? ''} onChange={(e) => set('point_worth', +e.target.value)} />
          {errors.point_worth && <p className="text-xs text-danger mt-1">{errors.point_worth}</p>}
        </div>
        <div>
          <label className="block text-xs font-medium text-mist mb-1">XP *</label>
          <input type="number" className={`input ${errors.xp_worth ? 'error' : ''}`} min={1}
            value={form.xp_worth ?? ''} onChange={(e) => set('xp_worth', +e.target.value)} />
          {errors.xp_worth && <p className="text-xs text-danger mt-1">{errors.xp_worth}</p>}
        </div>
      </div>

      {/* Start + Deadline */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Start At *</label>
          <input type="datetime-local" className="input"
            value={form.start_at?.slice(0, 16) ?? ''} onChange={(e) => set('start_at', e.target.value)} />
        </div>
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Deadline</label>
          <input type="datetime-local" className="input"
            value={form.deadline_at?.slice(0, 16) ?? ''} onChange={(e) => set('deadline_at', e.target.value)} />
        </div>
      </div>

      {/* Competition-specific */}
      {form.quest_type === 'competition' && (
        <div className="grid grid-cols-2 gap-3 p-3 rounded-lg"
          style={{ background: 'rgba(251,191,36,0.06)', border: '1px solid rgba(251,191,36,0.15)' }}>
          <div>
            <label className="block text-xs font-medium text-gold mb-1">Winner Reward (pts) *</label>
            <input type="number" className={`input ${errors.winner_point_reward ? 'error' : ''}`} min={1}
              value={form.winner_point_reward ?? ''} onChange={(e) => set('winner_point_reward', +e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gold mb-1">Runner-up Reward (pts)</label>
            <input type="number" className="input" min={0}
              value={form.runner_up_point_reward ?? ''} onChange={(e) => set('runner_up_point_reward', +e.target.value)} />
          </div>
        </div>
      )}

      {/* Group-specific */}
      {form.quest_type === 'group' && (
        <div className="p-3 rounded-lg space-y-2"
          style={{ background: 'rgba(248,113,113,0.06)', border: '1px solid rgba(248,113,113,0.15)' }}>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={!!form.has_collective_deadline}
              onChange={(e) => set('has_collective_deadline', e.target.checked)} />
            <span className="text-mist">Has collective deadline</span>
          </label>
          {form.has_collective_deadline && (
            <div>
              <label className="block text-xs font-medium text-mist mb-1">Collective Deadline</label>
              <input type="datetime-local" className="input"
                value={form.collective_deadline_at?.slice(0, 16) ?? ''}
                onChange={(e) => set('collective_deadline_at', e.target.value)} />
            </div>
          )}
        </div>
      )}

      {/* Submit */}
      <div className="flex justify-end gap-3 pt-2">
        <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
          {mutation.isPending
            ? <Spinner size={16} />
            : mode === 'sanctum' ? 'Create Quest' : 'Submit Proposal'}
        </button>
      </div>
    </form>
  )
}
