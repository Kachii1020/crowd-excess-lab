import { useEffect, useState, type FormEvent } from 'react'
import {
  Activity, BookOpenCheck, Bot, CheckCircle2, CircleDashed, Database,
  FileSearch, Menu, Search, ShieldCheck, SlidersHorizontal, WalletCards, X,
} from 'lucide-react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAgentStatus, useLineage, useRuns } from '../api/queries.ts'
import type { AgentStatus, LineageResponse } from '../api/schemas.ts'

export type WorkspaceContext = { runId: string }

const navigation = [
  { to: '/agent', label: 'Agent Console', icon: Bot },
  { to: '/portfolio', label: 'Paper Portfolio', icon: WalletCards },
  { to: '/strategy', label: 'Strategy & Risk', icon: SlidersHorizontal },
  { to: '/research', label: 'Research Origin', icon: BookOpenCheck },
  { to: '/events', label: 'Korea Event Study', icon: FileSearch },
  { to: '/lineage', label: 'Data Lineage', icon: Database },
]

function AgentProvenanceRail({ status, lineage }: {
  status?: AgentStatus,
  lineage?: LineageResponse,
}) {
  const sourceKeys = Object.keys(status?.sources ?? {})
  const sourceReady = (prefix: string) => sourceKeys.some((key) => key.startsWith(prefix))
  const items = [
    { name: 'NAVER', ready: sourceReady('naver_'), detail: 'Search attention' },
    { name: 'Alpaca', ready: sourceReady('alpaca_market_'), detail: 'Market + options' },
    { name: 'OpenAI', ready: Boolean(status?.last_run), detail: 'News evidence' },
    { name: 'Risk Engine', ready: Boolean(status?.last_run), detail: 'Deterministic gates' },
    {
      name: 'Audit Store',
      ready: Boolean(status?.configured),
      detail: status?.configured ? 'Append-only' : 'Not connected',
    },
  ]

  return (
    <section className="provenance-rail agent-provenance" aria-label="Agent provenance">
      <div className="provenance-title"><Activity aria-hidden="true" /><span>Decision Lineage</span></div>
      {items.map((source) => (
        <div className="provenance-source" data-ready={source.ready} key={source.name}>
          {source.ready ? <CheckCircle2 aria-hidden="true" /> : <CircleDashed aria-hidden="true" />}
          <span><strong>{source.name}</strong><small>{source.detail}</small></span>
        </div>
      ))}
      <div className="provenance-run">
        <span>LATEST RUN</span>
        <strong>{status?.last_run?.run_id ?? 'No autonomous run yet'}</strong>
        {lineage && <small>{lineage.total} retained research snapshots</small>}
      </div>
    </section>
  )
}

export function AppShell() {
  const runs = useRuns()
  const agentStatus = useAgentStatus()
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
    const query = search.trim().toUpperCase()
    navigate(query ? `/agent?symbol=${encodeURIComponent(query)}` : '/agent')
  }

  const selectedRunId = runId || runs.data?.[0]?.run_id || ''
  const lineage = useLineage(selectedRunId)
  const hasResearch = Boolean(runs.data?.length)
  const connected = Boolean(agentStatus.data?.configured)

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="global-header">
        <Link className="brand" to="/agent" aria-label="Crowd Excess Agent home">
          <strong>CROWD EXCESS</strong><span>AGENT</span>
        </Link>
        <button className="icon-button mobile-menu" type="button" aria-label="Open navigation" onClick={() => setMobileOpen(true)}><Menu aria-hidden="true" /></button>
        <form className="command-search" role="search" onSubmit={onSearch}>
          <Search aria-hidden="true" />
          <label className="sr-only" htmlFor="global-search">Inspect a universe symbol</label>
          <input id="global-search" name="global-search" autoComplete="off" spellCheck={false} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Inspect AAPL, MSFT, NVDA, TSLA, or QQQ…" />
          <kbd>⌘ K</kbd>
        </form>
        <div className="header-actions">
          <span className="research-mode"><span className={connected ? 'signal-dot' : 'signal-dot signal-dot--off'} />{connected ? 'Audit Connected' : 'Setup Pending'}</span>
          <span className="mode-chip"><ShieldCheck aria-hidden="true" />{agentStatus.data?.mode?.toUpperCase() ?? 'SHADOW'} ONLY</span>
          <label className="run-select research-run-select">
            <span>RESEARCH</span>
            <select name="research-run" aria-label="Select Korean research run" value={selectedRunId} onChange={(event) => setRunId(event.target.value)} disabled={!hasResearch}>
              {!hasResearch && <option value="">No run</option>}
              {runs.data?.map((run) => <option value={run.run_id} key={run.run_id}>{run.run_id}</option>)}
            </select>
          </label>
        </div>
      </header>

      <aside className={`sidebar ${mobileOpen ? 'sidebar--open' : ''}`}>
        <div className="sidebar-mobile-head"><span>Navigation</span><button className="icon-button sidebar-close" type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)}><X aria-hidden="true" /></button></div>
        <nav aria-label="Primary navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} aria-label={label} title={label} onClick={() => setMobileOpen(false)}>
              <Icon aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="connection-line"><span className={connected ? 'signal-dot' : 'signal-dot signal-dot--off'} />{connected ? 'Public audit ready' : 'Waiting for Supabase'}</div>
          <p>PAPER OPTIONS / DEFINED RISK</p>
        </div>
      </aside>

      <div className="workspace">
        <main id="main-content" tabIndex={-1}>
          <Outlet context={{ runId: selectedRunId } satisfies WorkspaceContext} />
        </main>
        <AgentProvenanceRail status={agentStatus.data} lineage={lineage.data} />
        <footer className="disclaimer">
          <ShieldCheck aria-hidden="true" /> Alpaca paper trading only. No live mode, naked options, investment advice, or profitability claim.
        </footer>
      </div>
      {mobileOpen && <button className="scrim" type="button" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    </div>
  )
}
