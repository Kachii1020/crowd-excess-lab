import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell.tsx'
import { ErrorBoundary } from './components/ErrorBoundary.tsx'
import { LoadingState } from './components/States.tsx'
import './App.css'

const OverviewPage = lazy(() => import('./pages/OverviewPage.tsx').then((module) => ({ default: module.OverviewPage })))
const EventsPage = lazy(() => import('./pages/EventsPage.tsx').then((module) => ({ default: module.EventsPage })))
const EventEvidencePage = lazy(() => import('./pages/EventEvidencePage.tsx').then((module) => ({ default: module.EventEvidencePage })))
const ResearchPage = lazy(() => import('./pages/ResearchPage.tsx').then((module) => ({ default: module.ResearchPage })))
const LineagePage = lazy(() => import('./pages/LineagePage.tsx').then((module) => ({ default: module.LineagePage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage.tsx').then((module) => ({ default: module.SettingsPage })))

function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingState label="Preparing the workbench" />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Navigate replace to="/events" />} />
            <Route path="dashboard" element={<OverviewPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="events/:receiptNumber" element={<EventEvidencePage />} />
            <Route path="research" element={<ResearchPage />} />
            <Route path="lineage" element={<LineagePage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate replace to="/events" />} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}

export default App
