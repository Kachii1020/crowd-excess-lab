import { useEffect, useState, type FormEvent } from 'react'
import {
  CheckCircle2, CircleDashed, Database, FileSearch, FlaskConical, LayoutDashboard,
  Menu, Search, Settings, ShieldCheck, X,
} from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useLineage, useRuns } from '../api/queries.ts'
import type { LineageResponse, ResearchRun } from '../api/schemas.ts'
import { format } from '../lib/format.ts'
import { ErrorState, LoadingState } from './States.tsx'

export type WorkspaceContext = { runId: string }

const navigation = [
  { to: '/events', label: 'Event Monitor', icon: FileSearch },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/research', label: 'Attention Excess', icon: FlaskConical },
  { to: '/lineage', label: 'Data Lineage', icon: Database },
  { to: '/settings', label: 'Connections', icon: Settings },
]

function ProvenanceRail({ run, lineage }: { run?: ResearchRun, lineage?: LineageResponse }) {
  const counts = run?.counts ?? {}
  const selected = counts.selected_events ?? 0
  const attention = counts.attention_observed ?? 0
  const prices = counts.decision_prices_observed ?? 0
  const observedOutcomes = counts.abnormal_h1_observed ?? 0
  const lineageTotal = lineage?.total ?? 0
  const retainedSnapshots = lineage?.groups.reduce((total, group) => total + group.retained_count, 0) ?? 0

  const sources = [
    { name: 'OpenDART', value: `${selected}/${run?.target_events ?? 0}`, ready: selected > 0, detail: 'Disclosure sample' },
    { name: 'NAVER', value: `${attention}/${selected}`, ready: selected > 0 && attention === selected, detail: 'Attention proxy' },
    { name: 'Price API', value: prices ? `${prices}/${selected}` : 'Pending', ready: prices > 0, detail: 'Decision prices' },
    { name: 'Outcomes', value: observedOutcomes ? `${observedOutcomes}/${selected}` : 'Pending', ready: observedOutcomes > 0, detail: 'Abnormal H1' },
    {
      name: 'Snapshots',
      value: `${format.integer(retainedSnapshots)}/${format.integer(lineageTotal)}`,
      ready: lineageTotal > 0 && retainedSnapshots === lineageTotal,
      detail: retainedSnapshots === lineageTotal ? 'Retained source files' : 'Metadata only',
    },
  ]

  return (
    <section className="provenance-rail" aria-label="Data provenance">
      <div className="provenance-title"><Database aria-hidden="true" /><span>Data Provenance</span></div>
      {sources.map((source) => (
        <div className="provenance-source" data-ready={source.ready} key={source.name}>
          {source.ready ? <CheckCircle2 aria-hidden="true" /> : <CircleDashed aria-hidden="true" />}
          <span><strong>{source.name} <b>{source.value}</b></strong><small>{source.detail}</small></span>
        </div>
      ))}
      <div className="provenance-run"><span>Run</span><strong>{run?.run_id ?? 'No run'}</strong></div>
    </section>
  )
}

export function AppShell() {
  const runs = useRuns()
  const [runId, setRunId] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        document.querySelector<HTMLInputElement>('#global-search')?.focus()
      }
      if (event.key === '/' && document.activeElement?.tagName !== 'INPUT') {
        event.preventDefault()
        document.querySelector<HTMLInputElement>('#global-search')?.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const onSearch = (event: FormEvent) => {
    event.preventDefault()
    const query = search.trim()
    navigate(query ? `/events?q=${encodeURIComponent(query)}` : '/events')
  }

  const selectedRunId = runId || runs.data?.[0]?.run_id || ''
  const selected = runs.data?.find((run) => run.run_id === selectedRunId)
  const lineage = useLineage(selectedRunId)
  const hasRuns = Boolean(runs.data?.length)

  if (runs.isLoading) return <LoadingState label="Discovering research runs" />
  if (runs.error) return <ErrorState error={runs.error} retry={() => void runs.refetch()} />

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="global-header">
        <Link className="brand" to="/events" aria-label="Crowd Excess Lab home">
          <strong>CROWD EXCESS</strong><span>LAB</span>
        </Link>
        <button className="icon-button mobile-menu" type="button" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu aria-hidden="true" /></button>
        <form className="command-search" role="search" onSubmit={onSearch}>
          <Search aria-hidden="true" />
          <label className="sr-only" htmlFor="global-search">Search securities or tickers</label>
          <input id="global-search" name="global-search" autoComplete="off" spellCheck={false} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search securities, tickers, or events…" />
          <kbd>⌘ K</kbd>
        </form>
        <div className="header-actions">
          <span className="research-mode"><span className="signal-dot" />Research Mode</span>
          <label className="run-select">
            <span>RUN</span>
            <select name="research-run" aria-label="Select research run" value={selectedRunId} onChange={(event) => setRunId(event.target.value)} disabled={!hasRuns}>
              {!hasRuns && <option value="">No run</option>}
              {runs.data?.map((run) => <option value={run.run_id} key={run.run_id}>{run.run_id}</option>)}
            </select>
          </label>
        </div>
      </header>

      <aside className={`sidebar ${mobileOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar-mobile-head"><span>Navigation</span><button className="icon-button sidebar-close" type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X aria-hidden="true" /></button></div>
        <nav aria-label="Primary navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} onClick={() => setMobileOpen(false)}>
              <Icon aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="connection-line"><span className={hasRuns ? 'signal-dot' : 'signal-dot signal-dot--off'} />{hasRuns ? 'Local artifacts ready' : 'No research run'}</div>
          <p>DESCRIPTIVE / IN-SAMPLE</p>
        </div>
      </aside>

      <div className="workspace">
        <main id="main-content" tabIndex={-1}>
          <Outlet context={{ runId: selectedRunId } satisfies WorkspaceContext} />
        </main>
        <ProvenanceRail run={selected} lineage={lineage.data} />
        <footer className="disclaimer">
          <ShieldCheck aria-hidden="true" /> Research use only. Results are descriptive and in-sample; this product provides no orders, recommendations, or profitability claims.
        </footer>
      </div>
      {mobileOpen && <button className="scrim" type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    </div>
  )
}
