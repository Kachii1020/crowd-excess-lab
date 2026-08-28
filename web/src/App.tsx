import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell.tsx'
import { ErrorBoundary } from './components/ErrorBoundary.tsx'
import { LoadingState } from './components/States.tsx'
import './App.css'

const EventsPage = lazy(() => import('./pages/EventsPage.tsx').then((module) => ({ default: module.EventsPage })))
const EventEvidencePage = lazy(() => import('./pages/EventEvidencePage.tsx').then((module) => ({ default: module.EventEvidencePage })))
const ResearchPage = lazy(() => import('./pages/ResearchPage.tsx').then((module) => ({ default: module.ResearchPage })))
const LineagePage = lazy(() => import('./pages/LineagePage.tsx').then((module) => ({ default: module.LineagePage })))
const AgentOverviewPage = lazy(() => import('./pages/AgentOverviewPage.tsx').then((module) => ({ default: module.AgentOverviewPage })))
const AgentConsolePage = lazy(() => import('./pages/AgentConsolePage.tsx').then((module) => ({ default: module.AgentConsolePage })))
const AgentRunPage = lazy(() => import('./pages/AgentRunPage.tsx').then((module) => ({ default: module.AgentRunPage })))
const PortfolioPage = lazy(() => import('./pages/PortfolioPage.tsx').then((module) => ({ default: module.PortfolioPage })))
const StrategyPage = lazy(() => import('./pages/StrategyPage.tsx').then((module) => ({ default: module.StrategyPage })))

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingState label="Preparing the workbench" />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Navigate replace to="/agent" />} />
            <Route path="agent" element={<AgentOverviewPage />} />
            <Route path="decisions" element={<AgentConsolePage />} />
            <Route path="agent/runs/:runId" element={<AgentRunPage />} />
            <Route path="portfolio" element={<PortfolioPage />} />
            <Route path="strategy" element={<StrategyPage />} />
            <Route path="dashboard" element={<Navigate replace to="/agent" />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="events/:receiptNumber" element={<EventEvidencePage />} />
            <Route path="research" element={<ResearchPage />} />
            <Route path="lineage" element={<LineagePage />} />
            <Route path="settings" element={<Navigate replace to="/strategy" />} />
            <Route path="*" element={<Navigate replace to="/agent" />} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}

export default App
