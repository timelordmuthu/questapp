// frontend/src/App.tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { useAuthStore } from './store/authStore'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import HomePage from './pages/HomePage'
import GuildPage from './pages/GuildPage'
import ProfilePage from './pages/ProfilePage'
import SanctumPage from './pages/SanctumPage'
import PublicProfilePage from './pages/PublicProfilePage'
import NotFoundPage from './pages/NotFoundPage'

// Layout
import AppLayout from './components/layout/AppLayout'

// Toast system
import { ToastProvider } from './components/ui/Toast'

// Guild modals (rendered globally so sidebar can open them)
import { CreateGuildModal, JoinGuildModal } from './components/guilds/GuildModals'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return !isAuthenticated ? <>{children}</> : <Navigate to="/" replace />
}

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <CreateGuildModal />
        <JoinGuildModal />
      <Routes>
        {/* Guest-only routes */}
        <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
        <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />
        <Route path="/forgot-password" element={<GuestRoute><ForgotPasswordPage /></GuestRoute>} />
        <Route path="/reset-password" element={<GuestRoute><ResetPasswordPage /></GuestRoute>} />

        {/* Protected routes inside AppLayout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<HomePage />} />
          <Route path="guilds/:guildId" element={<GuildPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="sanctum" element={<SanctumPage />} />
          <Route path="u/:playerName" element={<PublicProfilePage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      </BrowserRouter>
    </ToastProvider>
  )
}
