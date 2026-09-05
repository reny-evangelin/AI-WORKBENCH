import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useTheme } from './hooks/useTheme'
import AppLayout from './layouts/AppLayout'
import HomePage from './pages/HomePage'
import DocumentsPage from './pages/DocumentsPage'
import PIDAnalysisPage from './pages/PIDAnalysisPage'
import KnowledgeBasePage from './pages/KnowledgeBasePage'
import ResultsPage from './pages/ResultsPage'
import ChatPage from './pages/chat/ChatPage'

export default function App() {
  const { theme, toggle } = useTheme()

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout theme={theme} onToggleTheme={toggle} />}>
          {/* "/" is the AI Assistant — chat-first default */}
          <Route path="/"                index element={<ChatPage />} />
          {/* /chat kept as alias so old links don't break */}
          <Route path="/chat"            element={<Navigate to="/" replace />} />
          {/* existing pages unchanged */}
          <Route path="/home"            element={<HomePage />} />
          <Route path="/documents"       element={<DocumentsPage />} />
          <Route path="/pid-analysis"    element={<PIDAnalysisPage />} />
          <Route path="/knowledge-base"  element={<KnowledgeBasePage />} />
          <Route path="/results"         element={<ResultsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
