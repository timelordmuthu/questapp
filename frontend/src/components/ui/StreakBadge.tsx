// frontend/src/components/ui/StreakBadge.tsx
interface StreakBadgeProps {
  type: 'daily' | 'weekly'
  count: number
}

export default function StreakBadge({ type, count }: StreakBadgeProps) {
  const icon = type === 'daily' ? '🔥' : '⚡'
  const label = type === 'daily' ? 'daily' : 'weekly'
  const color = count > 0 ? 'var(--color-ember-light)' : 'var(--color-mist-dark)'

  return (
    <span
      className="flex items-center gap-1 text-xs font-semibold"
      style={{ color }}
      title={`${count} ${label} streak`}
    >
      {icon} {count}
      <span className="font-normal text-mist-dark">{label}</span>
    </span>
  )
}
