// frontend/src/pages/ForgotPasswordPage.tsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import { authApi } from '../api/auth'
import Spinner from '../components/ui/Spinner'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)

  const submit = useMutation({
    mutationFn: () => authApi.forgotPassword(email),
    onSuccess: () => setSent(true),
  })

  return (
    <div className="min-h-screen flex items-center justify-center p-4" style={{ background: 'var(--color-void)' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="font-display text-3xl font-black gold-text">⚔ Quest</h1>
        </div>

        <div className="card">
          <h2 className="font-display text-lg font-bold text-mist-light mb-4 text-center">Recover Access</h2>

          {sent ? (
            <div className="text-center py-4">
              <p className="text-success text-sm mb-2">✓ If that email is registered, a reset link has been sent.</p>
              <p className="text-mist-dark text-xs">Check your inbox (and spam folder).</p>
              <Link to="/login" className="btn btn-ghost mt-4 text-xs inline-flex">← Back to Login</Link>
            </div>
          ) : (
            <form onSubmit={(e) => { e.preventDefault(); submit.mutate() }} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-mist mb-1">Email Address</label>
                <input type="email" className="input" placeholder="you@example.com"
                  value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <button type="submit" className="btn btn-primary w-full" disabled={submit.isPending}>
                {submit.isPending ? <Spinner size={18} /> : 'Send Reset Link'}
              </button>
              <p className="text-center">
                <Link to="/login" className="text-xs text-mist-dark hover:text-arcane-light transition-colors">
                  ← Back to Login
                </Link>
              </p>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  )
}
