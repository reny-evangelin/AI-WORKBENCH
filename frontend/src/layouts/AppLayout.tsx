// src/layouts/AppLayout.tsx
import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import type { Theme } from '../types'

interface AppLayoutProps {
  theme: Theme
  onToggleTheme: () => void
}

export default function AppLayout({ theme, onToggleTheme }: AppLayoutProps) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="app-layout">
      <Sidebar
        theme={theme}
        onToggleTheme={onToggleTheme}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed((c) => !c)}
      />
      <main
        className="main-content"
        style={{ transition: 'margin-left 0.22s ease' }}
      >
        <Outlet />
      </main>
    </div>
  )
}
