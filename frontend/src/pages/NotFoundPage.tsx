// frontend/src/pages/NotFoundPage.tsx
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function NotFoundPage() {
  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: 'var(--color-void)' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <p className="text-8xl mb-6">🌑</p>
        <h1 className="font-display text-4xl font-black text-mist-light mb-3">404</h1>
        <p className="font-display text-xl text-mist-dark mb-2">The void holds no path here.</p>
        <p className="text-sm text-mist-dark mb-8">
          This page does not exist in the realm.
        </p>
        <Link to="/" className="btn btn-primary">
          Return to the Quest Feed
        </Link>
      </motion.div>
    </div>
  )
}
