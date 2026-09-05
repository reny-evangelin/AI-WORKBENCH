import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Apply initial theme before React renders to avoid flash
const saved = localStorage.getItem('aiw-theme') ?? 'light'
document.documentElement.classList.add(saved)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
