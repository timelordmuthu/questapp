// frontend/src/store/uiStore.ts
import { create } from 'zustand'

interface UIState {
  leftSidebarOpen: boolean
  rightSidebarOpen: boolean
  activeGuildId: string | null
  activeModal: string | null
  modalData: Record<string, unknown>

  setLeftSidebar: (open: boolean) => void
  setRightSidebar: (open: boolean) => void
  setActiveGuild: (guildId: string | null) => void
  openModal: (name: string, data?: Record<string, unknown>) => void
  closeModal: () => void
}

export const useUIStore = create<UIState>((set) => ({
  leftSidebarOpen: true,
  rightSidebarOpen: true,
  activeGuildId: null,
  activeModal: null,
  modalData: {},

  setLeftSidebar: (open) => set({ leftSidebarOpen: open }),
  setRightSidebar: (open) => set({ rightSidebarOpen: open }),
  setActiveGuild: (guildId) => set({ activeGuildId: guildId }),
  openModal: (name, data = {}) => set({ activeModal: name, modalData: data }),
  closeModal: () => set({ activeModal: null, modalData: {} }),
}))
