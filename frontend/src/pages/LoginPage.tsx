// frontend/src/pages/LoginPage.tsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { Eye, EyeOff } from 'lucide-react'
import { authApi } from '../api/auth'
import { usersApi } from '../api/users'
import { useAuthStore } from '../store/authStore'
import Spinner from '../components/ui/Spinner'

export default function LoginPage() {
  const navigate = useNavigate()
  const setUser = useAuthStore((s) => s.setUser)
  const [form, setForm] = useState({ player_name: '', password: '' })
  const [showPw, setShowPw] = useState(false)
  const [hint, setHint]     = useState<string | null>(null)
  const [error, setError]   = useState<string | null>(null)

  const login = useMutation({
    mutationFn: () => authApi.login(form),
    onSuccess: async () => {
      const me = await usersApi.getMe().then((r) => r.data)
      setUser(me)
      navigate('/')
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail
      if (detail === 'no_account') {
        setError('No account found with that Player Name.')
      } else if (typeof detail === 'object' && detail?.error === 'wrong_password') {
        setHint(detail.hint)
        setError('Wrong password.')
      } else {
        setError(detail ?? 'Login failed.')
      }
    },
  })

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'var(--color-void)' }}
    >
      {/* Background glow orbs */}
      <div className="glow-orb w-96 h-96 -top-20 -left-20"
        style={{ background: 'var(--color-arcane)', position: 'fixed' }} />
      <div className="glow-orb w-64 h-64 bottom-0 right-0"
        style={{ background: 'var(--color-gold-dark)', position: 'fixed' }} />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md relative"
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-black gold-text mb-2">⚔ Quest</h1>
          <p className="text-mist-dark text-sm">Forge your legend with your Guild.</p>
        </div>

        <div className="card" style={{ boxShadow: 'var(--shadow-arcane)' }}>
          <h2 className="font-display text-xl font-bold text-mist-light mb-6 text-center">
            Enter the Realm
          </h2>

          <form
            onSubmit={(e) => { e.preventDefault(); setError(null); setHint(null); login.mutate() }}
            className="space-y-4"
          >
            <div>
              <label className="block text-xs font-medium text-mist mb-1">Player Name</label>
              <input
                className="input"
                placeholder="YourPlayerName"
                autoComplete="username"
                value={form.player_name}
                onChange={(e) => setForm((p) => ({ ...p, player_name: e.target.value }))}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-mist mb-1">Password</label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  className="input pr-10"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  value={form.password}
                  onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-mist-dark hover:text-mist-light"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {hint && (
                <p className="text-xs mt-1" style={{ color: 'var(--color-gold)' }}>
                  Hint: {hint}
                </p>
              )}
            </div>

            {error && (
              <p className="text-xs text-danger bg-danger/10 border border-danger/20 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button type="submit" className="btn btn-primary w-full mt-2" disabled={login.isPending}>
              {login.isPending ? <Spinner size={18} /> : 'Login'}
            </button>
          </form>

          <div className="flex justify-between mt-4 text-xs text-mist-dark">
            <Link to="/forgot-password" className="hover:text-arcane-light transition-colors">
              Forgot password?
            </Link>
            <Link to="/register" className="hover:text-arcane-light transition-colors">
              New here? Register →
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  )
}
