// frontend/src/components/layout/TopBar.tsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bell, Menu, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../store/authStore'
import { useUIStore } from '../../store/uiStore'
import { notificationsApi } from '../../api/quests'
import { authApi } from '../../api/auth'
import Avatar from '../ui/Avatar'
import NotificationPanel from '../notifications/NotificationPanel'

export default function TopBar() {
  const { user, clearUser } = useAuthStore()
  const { leftSidebarOpen, setLeftSidebar } = useUIStore()
  const navigate = useNavigate()
  const [showNotifs, setShowNotifs] = useState(false)

  const { data: unreadData } = useQuery({
    queryKey: ['notif-unread'],
    queryFn: () => notificationsApi.unreadCount().then((r) => r.data),
    refetchInterval: 30_000,
  })

  const handleLogout = async () => {
    await authApi.logout().catch(() => {})
    clearUser()
    navigate('/login')
  }

  return (
    <header
      className="sticky top-0 z-40 flex items-center justify-between px-4 py-3"
      style={{
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-surface-border)',
      }}
    >
      {/* Left: hamburger + logo */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setLeftSidebar(!leftSidebarOpen)}
          className="text-mist-dark hover:text-arcane-light transition-colors p-1 rounded"
        >
          {leftSidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
        <Link to="/" className="font-display text-xl font-bold gold-text select-none">
          ⚔ Quest
        </Link>
      </div>

      {/* Right: notifications + avatar */}
      <div className="flex items-center gap-3">
        {/* Notification bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifs(!showNotifs)}
            className="relative p-2 rounded-lg text-mist-dark hover:text-arcane-light transition-colors"
          >
            <Bell size={18} />
            {(unreadData?.unread_count ?? 0) > 0 && (
              <span
                className="absolute -top-1 -right-1 text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center"
                style={{ background: 'var(--color-ember)', color: 'white', fontSize: '10px' }}
              >
                {unreadData!.unread_count > 9 ? '9+' : unreadData!.unread_count}
              </span>
            )}
          </button>
          {showNotifs && <NotificationPanel onClose={() => setShowNotifs(false)} />}
        </div>

        {/* Avatar + dropdown */}
        {user && (
          <div className="relative group">
            <button className="flex items-center gap-2">
              <Avatar url={user.avatar_url} name={user.player_name} size={32} />
              <span className="hidden md:block text-sm text-mist-light font-medium">
                {user.player_name}
              </span>
            </button>
            <div
              className="absolute right-0 top-full mt-1 w-48 rounded-lg overflow-hidden opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none group-hover:pointer-events-auto z-50"
              style={{
                background: 'var(--color-void-100)',
                border: '1px solid var(--color-surface-border)',
              }}
            >
              <Link to="/profile" className="block px-4 py-2.5 text-sm text-mist hover:text-arcane-light hover:bg-surface transition-colors">
                My Profile
              </Link>
              <Link to="/sanctum" className="block px-4 py-2.5 text-sm text-mist hover:text-arcane-light hover:bg-surface transition-colors">
                My Sanctum
              </Link>
              <hr style={{ borderColor: 'var(--color-surface-border)' }} />
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2.5 text-sm text-danger hover:bg-surface transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
