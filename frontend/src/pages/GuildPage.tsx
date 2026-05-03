// frontend/src/pages/GuildPage.tsx
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Plus, Trophy, Users, RefreshCw, Crown, LogOut, Shield } from 'lucide-react'
import { guildsApi } from '../api/quests'
import { leaderboardApi } from '../api/quests'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import QuestCard from '../components/quests/QuestCard'
import QuestCreateForm from '../components/quests/QuestCreateForm'
import Modal from '../components/ui/Modal'
import Avatar from '../components/ui/Avatar'
import Spinner from '../components/ui/Spinner'
import { useToast } from '../components/ui/Toast'
import { questsApi } from '../api/quests'
import type { QuestCreatePayload } from '../api/quests'

type Tab = 'quests' | 'proposals' | 'members' | 'leaderboard'

export default function GuildPage() {
  const { guildId } = useParams<{ guildId: string }>()
  const { user } = useAuthStore()
  const { setActiveGuild } = useUIStore()
  const { toast } = useToast()
  const qc = useQueryClient()
  const [tab, setTab] = useState<Tab>('quests')
  const [showPropose, setShowPropose] = useState(false)
  const [lbType, setLbType] = useState<'all_time' | 'seasonal'>('all_time')

  useEffect(() => {
    if (guildId) setActiveGuild(guildId)
    return () => setActiveGuild(null)
  }, [guildId])

  const { data: guild, isLoading } = useQuery({
    queryKey: ['guild', guildId],
    queryFn: () => guildsApi.get(guildId!).then((r) => r.data),
    enabled: !!guildId,
  })

  const { data: feedData } = useQuery({
    queryKey: ['quest-feed', 'guild', guildId],
    queryFn: () => questsApi.getFeed({ page_size: 50 }).then((r) => r.data),
    enabled: tab === 'quests',
  })

  const { data: proposals } = useQuery({
    queryKey: ['proposals', guildId],
    queryFn: () => guildsApi.listProposals(guildId!).then((r) => r.data),
    enabled: tab === 'proposals' && !!guildId,
  })

  const { data: leaderboard } = useQuery({
    queryKey: ['leaderboard', guildId, lbType],
    queryFn: () => leaderboardApi.get(guildId!, lbType).then((r) => r.data),
    enabled: tab === 'leaderboard' && !!guildId,
  })

  const regenerateSigil = useMutation({
    mutationFn: () => guildsApi.regenerateSigil(guildId!),
    onSuccess: (r) => {
      toast(`New Sigil Code: ${r.data.sigil_code}`, 'success')
      qc.invalidateQueries({ queryKey: ['guild', guildId] })
    },
  })

  const voteOnProposal = useMutation({
    mutationFn: ({ pid, vote }: { pid: string; vote: string }) =>
      guildsApi.voteProposal(pid, vote),
    onSuccess: () => {
      toast('Vote recorded.', 'success')
      qc.invalidateQueries({ queryKey: ['proposals', guildId] })
    },
    onError: (err: any) => toast(err.response?.data?.detail ?? 'Failed.', 'error'),
  })

  if (isLoading) {
    return <div className="flex justify-center py-20"><Spinner size={32} /></div>
  }
  if (!guild) {
    return <p className="text-center text-mist-dark py-20">Guild not found.</p>
  }

  const isGM = user?.id === guild.guild_master_id?.toString?.() ||
               String(user?.id) === String(guild.guild_master_id)

  const TABS: { id: Tab; label: string; icon: any }[] = [
    { id: 'quests',      label: 'Quests',      icon: Shield },
    { id: 'proposals',   label: 'Proposals',   icon: Plus },
    { id: 'members',     label: 'Members',     icon: Users },
    { id: 'leaderboard', label: 'Rankings',    icon: Trophy },
  ]

  // Filter feed to only this guild's quests
  const guildQuests = (feedData?.items ?? []).filter(
    (q: any) => q.source === guild.name
  )

  return (
    <div className="max-w-3xl mx-auto">
      {/* Guild header */}
      <div className="card mb-6"
        style={{ background: 'linear-gradient(135deg, rgba(107,63,160,0.1), transparent)' }}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Shield size={18} style={{ color: 'var(--color-arcane-glow)' }} />
              <h1 className="font-display text-2xl font-bold text-mist-light">{guild.name}</h1>
            </div>
            <p className="text-sm text-mist-dark">{guild.member_count}/20 members</p>
          </div>

          <div className="flex flex-col items-end gap-2">
            {isGM && (
              <>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-mist-dark">Sigil:</span>
                  <span className="font-mono text-sm font-bold text-gold">{guild.sigil_code}</span>
                  <button
                    onClick={() => regenerateSigil.mutate()}
                    className="text-mist-dark hover:text-arcane-light transition-colors"
                    title="Regenerate Sigil Code"
                  >
                    <RefreshCw size={13} />
                  </button>
                </div>
                <span className="text-xs text-gold flex items-center gap-1">
                  <Crown size={11} /> Guild Master
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-5 p-1 rounded-lg" style={{ background: 'var(--color-surface)' }}>
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-medium transition-all"
            style={{
              background: tab === id ? 'var(--color-arcane)' : 'transparent',
              color:      tab === id ? 'white'               : 'var(--color-mist-dark)',
            }}
          >
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'quests' && (
        <div>
          <div className="flex justify-end mb-4">
            <button onClick={() => setShowPropose(true)} className="btn btn-primary gap-2 text-sm">
              <Plus size={14} /> Propose Quest
            </button>
          </div>
          {guildQuests.length === 0 ? (
            <p className="text-center text-mist-dark py-12">No active quests. Propose one!</p>
          ) : (
            <div className="space-y-3">
              {guildQuests.map((q: any) => <QuestCard key={q.instance_id} quest={q} />)}
            </div>
          )}
        </div>
      )}

      {tab === 'proposals' && (
        <div className="space-y-3">
          {!proposals?.length ? (
            <p className="text-center text-mist-dark py-12">No pending proposals.</p>
          ) : (
            proposals.map((p: any) => (
              <div key={p.id} className="card">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-mist-light">{p.proposed_data?.title}</h3>
                    <p className="text-xs text-mist-dark mt-0.5">
                      by {p.proposed_by} · {p.vote_count} vote{p.vote_count !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <span className="badge-pill type-occasional text-xs">
                    {p.proposed_data?.quest_type}
                  </span>
                </div>
                <p className="text-sm text-mist mb-3 line-clamp-2">{p.proposed_data?.description}</p>
                {!p.user_voted && (
                  <div className="flex gap-2">
                    {['accept', 'decline', 'suggest_changes'].map((v) => (
                      <button
                        key={v}
                        className={`btn text-xs py-1.5 px-3 ${v === 'accept' ? 'btn-primary' : v === 'decline' ? 'btn-danger' : 'btn-ghost'}`}
                        onClick={() => voteOnProposal.mutate({ pid: p.id, vote: v })}
                        disabled={voteOnProposal.isPending}
                      >
                        {v === 'accept' ? 'Accept' : v === 'decline' ? 'Decline' : 'Suggest Changes'}
                      </button>
                    ))}
                  </div>
                )}
                {p.user_voted && (
                  <p className="text-xs text-success">✓ You voted</p>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'members' && (
        <div className="space-y-2">
          {guild.members?.map((m: any) => (
            <div key={m.user_id} className="card flex items-center gap-3">
              <Avatar url={m.avatar_url} name={m.player_name} size={40} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-mist-light">{m.player_name}</span>
                  {m.is_guild_master && (
                    <span className="text-gold text-xs flex items-center gap-0.5"><Crown size={10} /> GM</span>
                  )}
                </div>
                <p className="text-xs text-mist-dark">Lv.{m.current_level} · {m.level_title}</p>
              </div>
              {m.last_active_at && (
                <span className="text-xs text-mist-dark">
                  Active {new Date(m.last_active_at).toLocaleDateString()}
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      {tab === 'leaderboard' && (
        <div>
          <div className="flex gap-2 mb-4">
            {(['all_time', 'seasonal'] as const).map((t) => (
              <button key={t} onClick={() => setLbType(t)}
                className="btn text-xs py-1.5"
                style={{
                  background: lbType === t ? 'var(--color-arcane)' : 'var(--color-surface)',
                  color:      lbType === t ? 'white' : 'var(--color-mist-dark)',
                  border: `1px solid ${lbType === t ? 'var(--color-arcane-light)' : 'var(--color-surface-border)'}`,
                }}>
                {t === 'all_time' ? 'All Time' : 'This Month'}
              </button>
            ))}
          </div>
          <div className="space-y-2">
            {leaderboard?.entries?.map((e: any) => (
              <motion.div key={e.user_id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                className="flex items-center gap-3 p-3 rounded-lg"
                style={{
                  background: e.is_current_user ? 'rgba(107,63,160,0.1)' : 'var(--color-surface-raised)',
                  border: `1px solid ${e.is_current_user ? 'rgba(107,63,160,0.3)' : 'var(--color-surface-border)'}`,
                }}>
                <span className="w-7 text-center text-sm font-bold"
                  style={{ color: e.rank === 1 ? 'var(--color-gold)' : e.rank === 2 ? '#cbd5e1' : e.rank === 3 ? 'var(--color-ember)' : 'var(--color-mist-dark)' }}>
                  {e.rank === 1 ? '👑' : e.rank === 2 ? '🥈' : e.rank === 3 ? '🥉' : e.rank}
                </span>
                <Avatar url={e.avatar_url} name={e.player_name} size={32} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-mist-light">{e.player_name}</p>
                  <p className="text-xs text-mist-dark">Lv.{e.current_level} {e.level_title}</p>
                </div>
                <span className="font-bold text-sm" style={{ color: 'var(--color-gold)' }}>
                  {e.points.toLocaleString()} pts
                </span>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Propose quest modal */}
      <Modal open={showPropose} onClose={() => setShowPropose(false)} title="Propose Quest" maxWidth="580px">
        <p className="text-xs text-mist-dark mb-4">
          Proposals go to a 48-hour vote. 60%+ of members must accept for it to activate.
        </p>
        <QuestCreateForm
          mode="guild"
          guildId={guildId}
          onSuccess={() => setShowPropose(false)}
          submitFn={(data: QuestCreatePayload) => guildsApi.submitProposal(guildId!, data)}
        />
      </Modal>
    </div>
  )
}
