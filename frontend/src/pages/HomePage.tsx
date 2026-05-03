// frontend/src/pages/HomePage.tsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Filter, Plus, Sword } from 'lucide-react'
import { questsApi } from '../api/quests'
import { sanctumApi, guildsApi } from '../api/quests'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import QuestCard from '../components/quests/QuestCard'
import QuestCreateForm from '../components/quests/QuestCreateForm'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import type { QuestCreatePayload } from '../api/quests'

const FILTER_TYPES = ['all', 'daily', 'weekly', 'occasional', 'competition', 'group']

export default function HomePage() {
  const { user } = useAuthStore()
  const { activeGuildId } = useUIStore()
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [showCreate, setShowCreate] = useState(false)
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['quest-feed', typeFilter, statusFilter, page],
    queryFn: () =>
      questsApi.getFeed({
        quest_type: typeFilter !== 'all' ? typeFilter : undefined,
        status:     statusFilter !== 'all' ? statusFilter : undefined,
        page,
        page_size: 20,
      }).then((r) => r.data),
  })

  const quests = data?.items ?? []
  const total  = data?.total  ?? 0

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-mist-light flex items-center gap-2">
            <Sword size={22} style={{ color: 'var(--color-arcane-glow)' }} />
            Quest Feed
          </h1>
          <p className="text-xs text-mist-dark mt-0.5">
            {total} active quest{total !== 1 ? 's' : ''} across your Guilds and Sanctum
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary gap-2">
          <Plus size={15} /> New Quest
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-5 flex-wrap">
        <Filter size={14} className="text-mist-dark flex-shrink-0" />
        <div className="flex gap-1 flex-wrap">
          {FILTER_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => { setTypeFilter(t); setPage(1) }}
              className="px-3 py-1 rounded-full text-xs font-medium transition-all"
              style={{
                background: typeFilter === t ? 'var(--color-arcane)' : 'var(--color-surface-raised)',
                color:      typeFilter === t ? 'white'               : 'var(--color-mist)',
                border:     typeFilter === t ? '1px solid var(--color-arcane-light)' : '1px solid var(--color-surface-border)',
              }}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex gap-1 ml-auto">
          {['all', 'done', 'missed'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1) }}
              className="px-2.5 py-1 rounded-full text-xs transition-all"
              style={{
                background: statusFilter === s ? 'rgba(107,63,160,0.2)' : 'transparent',
                color:      statusFilter === s ? 'var(--color-arcane-glow)' : 'var(--color-mist-dark)',
                border:     statusFilter === s ? '1px solid var(--color-arcane)' : '1px solid transparent',
              }}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Quest list */}
      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner size={32} /></div>
      ) : quests.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <p className="text-5xl mb-4">⚔️</p>
          <p className="font-display text-lg text-mist-dark">No quests found.</p>
          <p className="text-xs text-mist-dark mt-1">
            Join a Guild or create a Sanctum quest to begin.
          </p>
        </motion.div>
      ) : (
        <div className="space-y-3">
          <AnimatePresence mode="popLayout">
            {quests.map((q: any) => (
              <QuestCard key={q.instance_id} quest={q} />
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Pagination */}
      {total > 20 && (
        <div className="flex justify-center gap-3 mt-6">
          <button
            className="btn btn-ghost text-xs"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Previous
          </button>
          <span className="text-xs text-mist-dark self-center">
            Page {page} of {Math.ceil(total / 20)}
          </span>
          <button
            className="btn btn-ghost text-xs"
            disabled={page * 20 >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}

      {/* Create quest modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Quest" maxWidth="580px">
        <QuestCreateForm
          mode="sanctum"
          onSuccess={() => setShowCreate(false)}
          submitFn={(data: QuestCreatePayload) => sanctumApi.createQuest(data)}
        />
      </Modal>
    </div>
  )
}
