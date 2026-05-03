// frontend/src/components/ui/Avatar.tsx
interface AvatarProps {
  url: string | null | undefined
  name: string
  size?: number
}

export default function Avatar({ url, name, size = 36 }: AvatarProps) {
  const initials = name
    .split(/[\s_]+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')

  if (url) {
    return (
      <img
        src={url}
        alt={name}
        width={size}
        height={size}
        className="rounded-full object-cover flex-shrink-0"
        style={{ width: size, height: size }}
      />
    )
  }

  return (
    <div
      className="rounded-full flex items-center justify-center flex-shrink-0 font-semibold select-none"
      style={{
        width: size,
        height: size,
        fontSize: size * 0.35,
        background: 'linear-gradient(135deg, var(--color-arcane-dark), var(--color-arcane))',
        color: 'white',
      }}
    >
      {initials}
    </div>
  )
}
