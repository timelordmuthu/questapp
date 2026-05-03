// frontend/src/pages/ResetPasswordPage.tsx
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api/auth'
import Spinner from '../components/ui/Spinner'

export default function ResetPasswordPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') ?? ''
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const reset = useMutation({
    mutationFn: () => authApi.resetPassword(token, password),
    onSuccess: () => navigate('/login', { state: { message: 'Password reset. You can now log in.' } }),
    onError: (err: any) => setError(err.response?.data?.detail ?? 'Reset failed.'),
  })

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--color-void)' }}>
        <div className="card text-center">
          <p className="text-danger mb-4">Invalid or missing reset token.</p>
          <Link to="/forgot-password" className="btn btn-ghost text-sm">Request a new link</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--color-void)' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="font-display text-3xl font-black gold-text">⚔ Quest</h1>
        </div>
        <div className="card">
          <h2 className="font-display text-lg font-bold text-mist-light mb-4 text-center">Set New Password</h2>
          <form onSubmit={(e) => { e.preventDefault(); setError(''); reset.mutate() }} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-mist mb-1">New Password (min 8 chars)</label>
              <input type="password" className="input" placeholder="••••••••"
                value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <p className="text-xs text-danger">{error}</p>}
            <button type="submit" className="btn btn-primary w-full" disabled={reset.isPending}>
              {reset.isPending ? <Spinner size={18} /> : 'Reset Password'}
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  )
}
