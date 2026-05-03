// frontend/src/components/layout/AppLayout.tsx
import { Outlet } from 'react-router-dom'
import LeftSidebar from './LeftSidebar'
import RightSidebar from './RightSidebar'
import TopBar from './TopBar'
import { useUIStore } from '../../store/uiStore'

export default function AppLayout() {
  const { leftSidebarOpen, rightSidebarOpen } = useUIStore()

  return (
    <div className="min-h-screen bg-void flex flex-col">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar */}
        <aside
          className={`hidden lg:block transition-all duration-300 ${
            leftSidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
          }`}
        >
          <LeftSidebar />
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>

        {/* Right sidebar */}
        <aside
          className={`hidden xl:block transition-all duration-300 ${
            rightSidebarOpen ? 'w-60' : 'w-0 overflow-hidden'
          }`}
        >
          <RightSidebar />
        </aside>
      </div>
    </div>
  )
}
