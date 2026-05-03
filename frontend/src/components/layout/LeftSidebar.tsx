// frontend/src/components/layout/LeftSidebar.tsx
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Home, Shield, Flame, Star, Plus, LogOut } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import { usersApi } from '../../api/users'
import { authApi } from '../../api/auth'
import Avatar from '../ui/Avatar'
import XPBar from '../ui/XPBar'
import StreakBadge from '../ui/StreakBadge'

export default function LeftSidebar() {
  const { user, clearUser } = useAuthStore()
  const { openModal } = useUIStore()
  const location = useLocation()
  const navigate = useNavigate()

  const { data: profile } = useQuery({
    queryKey: ['me'],
    queryFn: () => usersApi.getMe().then((r) => r.data),
    enabled: !!user,
  })

  const me = profile ?? user

  const navItems = [
    { to: '/', icon: Home, label: 'Quest Feed' },
    { to: '/sanctum', icon: Flame, label: 'My Sanctum' },
    { to: '/profile', icon: Star, label: 'My Profile' },
  ]

  const handleLogout = async () => {
    await authApi.logout().catch(() => {})
    clearUser()
    navigate('/login')
  }

  return (
    <div
      className="h-full flex flex-col py-4 px-3"
      style={{ background: 'var(--color-surface)', borderRight: '1px solid var(--color-surface-border)' }}
    >
      {/* User card */}
      {me && (
        <Link to="/profile" className="block p-3 rounded-lg mb-4 hover:bg-void-100 transition-colors group">
          <div className="flex items-center gap-3 mb-3">
            <Avatar url={me.avatar_url} name={me.player_name} size={40} />
            <div className="min-w-0">
              <p className="text-sm font-semibold text-mist-light truncate">{me.player_name}</p>
              <p className="text-xs text-arcane-light">
                Lv.{me.current_level} · {me.level_title}
              </p>
            </div>
          </div>
          <XPBar current={me.total_xp} toNext={me.xp_to_next_level} />
          <div className="flex gap-3 mt-2">
            <StreakBadge type="daily" count={me.daily_streak} />
            <StreakBadge type="weekly" count={me.weekly_streak} />
          </div>
        </Link>
      )}

      {/* Nav */}
      <nav className="space-y-1 flex-1">
        {navItems.map(({ to, icon: Icon, label }) => {
          const active = location.pathname === to
          return (
            <Link
              key={to}
              to={to}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
              style={{
                color: active ? 'var(--color-arcane-glow)' : 'var(--color-mist)',
                background: active ? 'rgba(107,63,160,0.15)' : 'transparent',
                borderLeft: active ? '2px solid var(--color-arcane-glow)' : '2px solid transparent',
              }}
            >
              <Icon size={16} />
              {label}
            </Link>
          )
        })}

        {/* Guilds section */}
        <div className="pt-4">
          <div className="flex items-center justify-between px-3 mb-2">
            <span className="text-xs font-semibold text-mist-dark uppercase tracking-wider">Guilds</span>
            <button
              onClick={() => openModal('createGuild')}
              className="text-mist-dark hover:text-arcane-light transition-colors"
              title="Create Guild"
            >
              <Plus size={14} />
            </button>
          </div>

          <GuildList />

          <button
            onClick={() => openModal('joinGuild')}
            className="flex items-center gap-2 px-3 py-2 w-full text-sm text-mist-dark hover:text-arcane-light transition-colors mt-1"
          >
            <Shield size={14} />
            Join via Sigil Code
          </button>
        </div>
      </nav>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="flex items-center gap-2 px-3 py-2 text-sm text-mist-dark hover:text-danger transition-colors rounded-lg mt-2"
      >
        <LogOut size={14} />
        Logout
      </button>
    </div>
  )
}

function GuildList() {
  const { user } = useAuthStore()
  const { data: profile } = useQuery({
    queryKey: ['me'],
    queryFn: () => usersApi.getMe().then((r) => r.data),
    enabled: !!user,
  })
  const location = useLocation()

  const guilds: Array<{ id: string; name: string }> = profile?.guild_memberships_summary ?? []

  if (guilds.length === 0) {
    return (
      <p className="px-3 py-2 text-xs text-mist-dark italic">No guilds yet.</p>
    )
  }

  return (
    <div className="space-y-1">
      {guilds.map((g) => {
        const active = location.pathname === `/guilds/${g.id}`
        return (
          <Link
            key={g.id}
            to={`/guilds/${g.id}`}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all truncate"
            style={{
              color: active ? 'var(--color-arcane-glow)' : 'var(--color-mist)',
              background: active ? 'rgba(107,63,160,0.15)' : 'transparent',
            }}
          >
            <Shield size={13} className="flex-shrink-0" />
            <span className="truncate">{g.name}</span>
          </Link>
        )
      })}
    </div>
  )
}
