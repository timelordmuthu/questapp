// frontend/src/pages/SanctumPage.tsx
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Plus, Flame } from 'lucide-react'
import { sanctumApi } from '../api/quests'
import { questsApi } from '../api/quests'
import QuestCard from '../components/quests/QuestCard'
import QuestCreateForm from '../components/quests/QuestCreateForm'
import Modal from '../components/ui/Modal'
import Spinner from '../components/ui/Spinner'
import type { QuestCreatePayload } from '../api/quests'

export default function SanctumPage() {
  const [showCreate, setShowCreate] = useState(false)

  const { data: feedData, isLoading } = useQuery({
    queryKey: ['sanctum-feed'],
    queryFn: () => questsApi.getFeed({ page_size: 50 }).then((r) => r.data),
  })

  const sanctumQuests = (feedData?.items ?? []).filter(
    (q: any) => q.source === 'Sanctum'
  )

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-mist-light flex items-center gap-2">
            <Flame size={22} style={{ color: 'var(--color-ember-light)' }} />
            My Sanctum
          </h1>
          <p className="text-xs text-mist-dark mt-0.5">
            Your private quest space — no voting, no approval.
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary gap-2">
          <Plus size={15} /> New Quest
        </button>
      </div>

      {/* Background lore text */}
      <div className="card mb-6 text-center py-6"
        style={{ background: 'linear-gradient(135deg, rgba(224,92,46,0.06), transparent)' }}>
        <p className="text-sm text-mist italic leading-relaxed max-w-md mx-auto">
          "The Sanctum is yours alone — a private flame that burns in the dark. 
          No Guild can claim these trials. Only you will know if they are completed."
        </p>
      </div>

      {/* Quests */}
      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner size={32} /></div>
      ) : sanctumQuests.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-16">
          <p className="text-5xl mb-4">🕯️</p>
          <p className="font-display text-lg text-mist-dark">The Sanctum awaits your first quest.</p>
          <button onClick={() => setShowCreate(true)} className="btn btn-primary mt-4 gap-2">
            <Plus size={15} /> Create First Quest
          </button>
        </motion.div>
      ) : (
        <div className="space-y-3">
          {sanctumQuests.map((q: any) => (
            <QuestCard key={q.instance_id} quest={q} />
          ))}
        </div>
      )}

      {/* Create modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Sanctum Quest" maxWidth="580px">
        <p className="text-xs text-mist-dark mb-4">
          Sanctum quests activate instantly. They count toward your XP, streaks, and personal history.
        </p>
        <QuestCreateForm
          mode="sanctum"
          onSuccess={() => setShowCreate(false)}
          submitFn={(data: QuestCreatePayload) => sanctumApi.createQuest(data)}
        />
      </Modal>
    </div>
  )
}
