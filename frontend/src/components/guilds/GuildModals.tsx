// frontend/src/components/guilds/GuildModals.tsx
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { guildsApi } from '../../api/quests'
import { useUIStore } from '../../store/uiStore'
import { useToast } from '../ui/Toast'
import Modal from '../ui/Modal'
import Spinner from '../ui/Spinner'

export function CreateGuildModal() {
  const { activeModal, closeModal } = useUIStore()
  const { toast } = useToast()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [name, setName] = useState('')

  const create = useMutation({
    mutationFn: () => guildsApi.create(name),
    onSuccess: (r) => {
      toast(`Guild "${r.data.name}" created! Sigil: ${r.data.sigil_code}`, 'success')
      qc.invalidateQueries({ queryKey: ['me'] })
      closeModal()
      navigate(`/guilds/${r.data.id}`)
    },
    onError: (err: any) => toast(err.response?.data?.detail ?? 'Failed.', 'error'),
  })

  return (
    <Modal open={activeModal === 'createGuild'} onClose={closeModal} title="Found a Guild">
      <p className="text-xs text-mist-dark mb-4">
        You'll be the Guild Master. A unique Sigil Code is generated automatically.
      </p>
      <form onSubmit={(e) => { e.preventDefault(); if (name.trim()) create.mutate() }} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Guild Name *</label>
          <input className="input" placeholder="E.g. Order of the Midnight Flame"
            value={name} onChange={(e) => setName(e.target.value)} maxLength={100} />
        </div>
        <button type="submit" className="btn btn-primary w-full" disabled={create.isPending || !name.trim()}>
          {create.isPending ? <Spinner size={16} /> : 'Create Guild'}
        </button>
      </form>
    </Modal>
  )
}

export function JoinGuildModal() {
  const { activeModal, closeModal } = useUIStore()
  const { toast } = useToast()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [code, setCode] = useState('')

  const join = useMutation({
    mutationFn: () => guildsApi.join(code.trim().toUpperCase()),
    onSuccess: (r) => {
      toast(`Joined ${r.data.name}!`, 'success')
      qc.invalidateQueries({ queryKey: ['me'] })
      closeModal()
      navigate(`/guilds/${r.data.id}`)
    },
    onError: (err: any) => toast(err.response?.data?.detail ?? 'Invalid Sigil Code.', 'error'),
  })

  return (
    <Modal open={activeModal === 'joinGuild'} onClose={closeModal} title="Join a Guild">
      <p className="text-xs text-mist-dark mb-4">
        Enter the 8-character Sigil Code shared by your Guild Master.
      </p>
      <form onSubmit={(e) => { e.preventDefault(); if (code.trim()) join.mutate() }} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-mist mb-1">Sigil Code *</label>
          <input
            className="input font-mono tracking-widest text-center text-lg uppercase"
            placeholder="A3KX92PQ"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''))}
            maxLength={8}
          />
        </div>
        <button type="submit" className="btn btn-primary w-full" disabled={join.isPending || code.length !== 8}>
          {join.isPending ? <Spinner size={16} /> : 'Join Guild'}
        </button>
      </form>
    </Modal>
  )
}
