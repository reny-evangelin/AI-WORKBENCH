// src/components/Sidebar.tsx
import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  ScanLine,
  BookOpen,
  BarChart3,
  Activity,
  Sun,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  SquarePen,
  Bot,
} from 'lucide-react'
import type { Theme } from '../types'

interface SidebarProps {
  theme: Theme
  onToggleTheme: () => void
  collapsed: boolean
  onToggleCollapse: () => void
}

// Navigation items below "New Chat" and the AI Assistant heading
const NAV_ITEMS = [
  { to: '/home',          label: 'Home',          icon: LayoutDashboard },
  { to: '/documents',     label: 'Documents',     icon: FileText },
  { to: '/pid-analysis',  label: 'P&ID Analysis', icon: ScanLine },
  { to: '/knowledge-base',label: 'Knowledge Base',icon: BookOpen },
  { to: '/results',       label: 'Results',       icon: BarChart3 },
]

export default function Sidebar({ theme, onToggleTheme, collapsed, onToggleCollapse }: SidebarProps) {
  const navigate = useNavigate()
  const w = collapsed ? 52 : 224

  return (
    <aside
      className="sidebar"
      style={{
        width: w,
        minWidth: w,
        transition: 'width 0.22s ease, min-width 0.22s ease',
        overflow: 'hidden',
      }}
    >
      {/* ── Top bar: logo + collapse toggle ─────────────── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          padding: collapsed ? '0.875rem 0' : '0.875rem 0.75rem 0.875rem 1rem',
          minHeight: 52,
          borderBottom: '1px solid var(--border)',
        }}
      >
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', minWidth: 0 }}>
            <div
              style={{
                width: 26, height: 26, borderRadius: 6,
                background: 'var(--primary)', flexShrink: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}
            >
              <Bot size={14} color="#fff" strokeWidth={2.2} />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: '0.8125rem', color: 'var(--text)', letterSpacing: '-0.01em', whiteSpace: 'nowrap' }}>
                AI Workbench
              </div>
              <div style={{ fontSize: '0.625rem', color: 'var(--muted)', letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                SIH 2026
              </div>
            </div>
          </div>
        )}

        {/* Collapse / expand button */}
        <button
          onClick={onToggleCollapse}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            flexShrink: 0,
            padding: '0.3rem',
            borderRadius: 6,
            border: 'none',
            background: 'transparent',
            color: 'var(--muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            transition: 'color 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--text)' }}
          onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--muted)' }}
        >
          {collapsed
            ? <PanelLeftOpen size={16} strokeWidth={2} />
            : <PanelLeftClose size={16} strokeWidth={2} />
          }
        </button>
      </div>

      {/* ── New Chat button ──────────────────────────────── */}
      <div style={{ padding: collapsed ? '0.625rem 0' : '0.625rem 0.625rem', borderBottom: '1px solid var(--border)' }}>
        <button
          onClick={() => navigate(`/?new=${Date.now()}`)}
          title="New Chat"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: '0.5rem',
            width: '100%',
            padding: collapsed ? '0.5rem' : '0.5rem 0.75rem',
            borderRadius: 7,
            border: '1px solid var(--border)',
            background: 'var(--panel)',
            color: 'var(--text)',
            fontSize: '0.8125rem',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            whiteSpace: 'nowrap',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--accent-bg)'
            e.currentTarget.style.borderColor = 'var(--primary)'
            e.currentTarget.style.color = 'var(--primary)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--panel)'
            e.currentTarget.style.borderColor = 'var(--border)'
            e.currentTarget.style.color = 'var(--text)'
          }}
        >
          <SquarePen size={14} strokeWidth={2} />
          {!collapsed && <span>New Chat</span>}
        </button>
      </div>

      {/* ── Navigation items ─────────────────────────────── */}
      <nav style={{ flex: 1, paddingTop: '0.375rem' }}>
        {!collapsed && (
          <div style={{ padding: '0.25rem 1rem 0.25rem' }}>
            <span className="section-label">Navigation</span>
          </div>
        )}

        {/* AI Assistant — primary item, goes to "/" */}
        <NavLink
          to="/"
          end
          className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
          title="AI Assistant"
          style={collapsed ? { justifyContent: 'center', padding: '0.5rem' } : undefined}
        >
          <Bot size={15} strokeWidth={2} />
          {!collapsed && 'AI Assistant'}
        </NavLink>

        {/* Standard nav items */}
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            title={label}
            style={collapsed ? { justifyContent: 'center', padding: '0.5rem' } : undefined}
          >
            <Icon size={15} strokeWidth={2} />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      {/* ── Bottom: system status + theme toggle ─────────── */}
      <div style={{ padding: collapsed ? '0.75rem 0' : '0.75rem 1rem', borderTop: '1px solid var(--border)' }}>
        {!collapsed && (
          <div style={{ marginBottom: '0.625rem' }}>
            <span className="section-label">System Status</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.3rem' }}>
              <Activity size={12} color="var(--primary)" />
              <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 500 }}>
                Local Processing: Active
              </span>
            </div>
          </div>
        )}

        {/* Theme toggle */}
        <button
          onClick={onToggleTheme}
          title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: '0.5rem',
            padding: collapsed ? '0.4rem' : '0.4rem 0.6rem',
            borderRadius: 6,
            border: '1px solid var(--border)',
            background: 'var(--panel)',
            color: 'var(--muted)',
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: 500,
            width: '100%',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--sidebar-hover)'
            e.currentTarget.style.color = 'var(--text)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--panel)'
            e.currentTarget.style.color = 'var(--muted)'
          }}
        >
          {theme === 'light' ? <Moon size={13} /> : <Sun size={13} />}
          {!collapsed && (theme === 'light' ? 'Dark mode' : 'Light mode')}
        </button>
      </div>
    </aside>
  )
}
