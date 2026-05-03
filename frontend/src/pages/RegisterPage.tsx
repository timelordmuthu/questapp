// frontend/src/pages/RegisterPage.tsx
import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation, useQuery } from '@tanstack/react-query'
import { CheckCircle, XCircle } from 'lucide-react'
import { authApi } from '../api/auth'
import { usersApi } from '../api/users'
import { useAuthStore } from '../store/authStore'
import Spinner from '../components/ui/Spinner'

const TIMEZONES = Intl.supportedValuesOf?.('timeZone') ?? [
  'UTC','Asia/Kolkata','America/New_York','America/Los_Angeles',
  'Europe/London','Europe/Berlin','Asia/Tokyo','Australia/Sydney',
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const setUser = useAuthStore((s) => s.setUser)

  const [form, setForm] = useState({
    full_name: '', player_name: '', email: '',
    password: '', password_hint: '',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone ?? 'UTC',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [pnCheck, setPnCheck] = useState<boolean | null>(null)
  const [pnDebounce, setPnDebounce] = useState('')

  const set = (k: string, v: string) => setForm((p) => ({ ...p, [k]: v }))

  // Debounce player name check
  useEffect(() => {
    const t = setTimeout(() => setPnDebounce(form.player_name), 500)
    return () => clearTimeout(t)
  }, [form.player_name])

  useQuery({
    queryKey: ['pn-check', pnDebounce],
    queryFn: () =>
      authApi.checkPlayerName(pnDebounce).then((r) => {
        setPnCheck(r.data.available)
        return r.data
      }),
    enabled: pnDebounce.length >= 3,
  })

  const validate = () => {
    const errs: Record<string, string> = {}
    if (!form.full_name.trim()) errs.full_name = 'Required.'
    if (!/^[a-zA-Z0-9_]{3,20}$/.test(form.player_name))
      errs.player_name = '3–20 alphanumeric or underscore.'
    if (pnCheck === false) errs.player_name = 'Player name already taken.'
    if (!form.email.includes('@')) errs.email = 'Valid email required.'
    if (form.password.length < 8) errs.password = 'Min 8 characters.'
    if (!form.password_hint.trim()) errs.password_hint = 'Required.'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const register = useMutation({
    mutationFn: () => authApi.register(form),
    onSuccess: async () => {
      await authApi.login({ player_name: form.player_name, password: form.password })
      const me = await usersApi.getMe().then((r) => r.data)
      setUser(me)
      navigate('/')
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail
      if (typeof detail === 'string') setErrors({ _: detail })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validate()) register.mutate()
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--color-void)' }}>
      <div className="glow-orb w-96 h-96 -top-20 -right-20" style={{ background: 'var(--color-arcane)', position: 'fixed' }} />

      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-lg">
        <div className="text-center mb-6">
          <h1 className="font-display text-3xl font-black gold-text mb-1">⚔ Quest</h1>
          <p className="text-mist-dark text-sm">Begin your legend.</p>
        </div>

        <div className="card">
          <h2 className="font-display text-xl font-bold text-mist-light mb-5 text-center">Create Account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full name */}
            <div>
              <label className="block text-xs font-medium text-mist mb-1">Full Name *</label>
              <input className={`input ${errors.full_name ? 'error' : ''}`} placeholder="Your real name"
                value={form.full_name} onChange={(e) => set('full_name', e.target.value)} />
              {errors.full_name && <p className="text-xs text-danger mt-1">{errors.full_name}</p>}
            </div>

            {/* Player name */}
            <div>
              <label className="block text-xs font-medium text-mist mb-1">
                Player Name * <span className="text-mist-dark font-normal">(permanent, 3–20 chars)</span>
              </label>
              <div className="relative">
                <input
                  className={`input pr-8 ${errors.player_name ? 'error' : ''}`}
                  placeholder="CoolWarrior42"
                  value={form.player_name}
                  onChange={(e) => { set('player_name', e.target.value); setPnCheck(null) }}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2">
                  {pnCheck === true  && <CheckCircle size={14} style={{ color: 'var(--color-success)' }} />}
                  {pnCheck === false && <XCircle     size={14} style={{ color: 'var(--color-danger)' }} />}
                </span>
              </div>
              {errors.player_name && <p className="text-xs text-danger mt-1">{errors.player_name}</p>}
              <p className="text-xs text-mist-dark mt-1">Cannot be changed after registration.</p>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-medium text-mist mb-1">Email *</label>
              <input type="email" className={`input ${errors.email ? 'error' : ''}`} placeholder="you@example.com"
                value={form.email} onChange={(e) => set('email', e.target.value)} />
              {errors.email && <p className="text-xs text-danger mt-1">{errors.email}</p>}
            </div>

            {/* Password + hint row */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-mist mb-1">Password *</label>
                <input type="password" className={`input ${errors.password ? 'error' : ''}`} placeholder="Min 8 chars"
                  value={form.password} onChange={(e) => set('password', e.target.value)} />
                {errors.password && <p className="text-xs text-danger mt-1">{errors.password}</p>}
              </div>
              <div>
                <label className="block text-xs font-medium text-mist mb-1">
                  Password Hint * <span className="text-mist-dark font-normal text-xs">(shown on wrong pw)</span>
                </label>
                <input className={`input ${errors.password_hint ? 'error' : ''}`} placeholder="E.g. My pet's name"
                  value={form.password_hint} onChange={(e) => set('password_hint', e.target.value)} />
              </div>
            </div>

            {/* Timezone */}
            <div>
              <label className="block text-xs font-medium text-mist mb-1">Timezone *</label>
              <select className="input" value={form.timezone} onChange={(e) => set('timezone', e.target.value)}>
                {TIMEZONES.map((tz) => <option key={tz} value={tz}>{tz}</option>)}
              </select>
            </div>

            {errors._ && (
              <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">{errors._}</p>
            )}

            <button type="submit" className="btn btn-primary w-full mt-2" disabled={register.isPending}>
              {register.isPending ? <Spinner size={18} /> : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-xs text-mist-dark mt-4">
            Already have an account?{' '}
            <Link to="/login" className="text-arcane-light hover:text-arcane-glow transition-colors">Login →</Link>
          </p>
        </div>
      </motion.div>
    </div>
  )
}
