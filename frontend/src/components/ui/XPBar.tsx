// frontend/src/components/ui/XPBar.tsx
interface XPBarProps {
  current: number
  toNext: number
}

export default function XPBar({ current, toNext }: XPBarProps) {
  const total = current + toNext
  const pct = total > 0 ? Math.min(100, (current / total) * 100) : 0
  return (
    <div>
      <div className="flex justify-between text-xs text-mist-dark mb-1">
        <span>{current.toLocaleString()} XP</span>
        <span>+{toNext.toLocaleString()} to next</span>
      </div>
      <div className="xp-bar-track">
        <div className="xp-bar-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
