import { useEffect, useRef, useState, type FormEvent } from 'react'
import {
  Activity, Archive, BookOpenCheck, Database, Ellipsis, FileSearch,
  LayoutDashboard, Search, ShieldCheck, SlidersHorizontal, WalletCards, X,
} from 'lucide-react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAgentStatus, useRuns } from '../api/queries.ts'

export type WorkspaceContext = { runId: string }

const primaryNavigation = [
  { to: '/agent', label: 'Overview', icon: LayoutDashboard },
  { to: '/decisions', label: 'Market Scan', icon: Activity },
  { to: '/portfolio', label: 'Portfolio', icon: WalletCards },
  { to: '/strategy', label: 'How It Works', icon: SlidersHorizontal },
]

const desktopNavigation = [
  ...primaryNavigation,
  { to: '/data', label: 'Data Health', icon: Database },
]

const archiveNavigation = [
  { to: '/research', label: 'Hypothesis', icon: BookOpenCheck },
  { to: '/events', label: 'Korea Events', icon: FileSearch },
  { to: '/lineage', label: 'Research Lineage', icon: Database },
]

export function AppShell() {
  const researchRuns = useRuns()
  const agentStatus = useAgentStatus()
  const [selectedResearchRunId, setSelectedResearchRunId] = useState('')
  const [moreOpen, setMoreOpen] = useState(false)
  const [search, setSearch] = useState('')
  const moreButton = useRef<HTMLButtonElement>(null)
  const moreSheet = useRef<HTMLDivElement>(null)
  const location = useLocation()
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

  useEffect(() => {
    if (!moreOpen) return
    const sheet = moreSheet.current
    const focusable = () => Array.from(sheet?.querySelectorAll<HTMLElement>('a, button:not([disabled])') ?? [])
    requestAnimationFrame(() => focusable()[0]?.focus())
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMoreOpen(false)
        requestAnimationFrame(() => moreButton.current?.focus())
        return
      }
      if (event.key !== 'Tab') return
      const items = focusable()
      if (!items.length) return
      const first = items[0]
      const last = items[items.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [moreOpen])

  const closeMore = () => {
    setMoreOpen(false)
    requestAnimationFrame(() => moreButton.current?.focus())
  }

  const onSearch = (event: FormEvent) => {
    event.preventDefault()
    const query = search.trim().toUpperCase()
    if (!query) {
      navigate('/decisions')
      return
    }
    const params = new URLSearchParams()
    const sampledRunId = agentStatus.data?.latest_sampled_run?.run_id
    if (sampledRunId) params.set('run', sampledRunId)
    params.set('symbol', query)
    navigate(`/decisions?${params.toString()}`)
  }

  const researchRunId = selectedResearchRunId || researchRuns.data?.[0]?.run_id || ''
  const connected = Boolean(agentStatus.data?.configured)
  const inResearchArchive = ['/research', '/events', '/lineage'].some(
    (path) => location.pathname === path || location.pathname.startsWith(`${path}/`),
  )
  const moreSectionActive = location.pathname === '/data' || inResearchArchive
  const primaryClass = (to: string, isActive: boolean) => (
    isActive || (to === '/decisions' && location.pathname.startsWith('/agent/runs/')) ? 'active' : undefined
  )

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Skip to content</a>
      <header className="global-header">
        <Link className="brand" to="/agent" aria-label="Crowd Excess Agent home">
          <strong>CROWD EXCESS</strong><span>AGENT</span>
        </Link>
        <form className="command-search" role="search" onSubmit={onSearch}>
          <Search aria-hidden="true" />
          <label className="sr-only" htmlFor="global-search">Inspect a Symbol in Market Scan</label>
          <input id="global-search" name="global-search" autoComplete="off" spellCheck={false} value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Inspect AAPL, MSFT, NVDA, TSLA, or QQQ…" />
          <kbd>⌘ K</kbd>
        </form>
        <div className="header-actions">
          <span className="research-mode"><span className={connected ? 'signal-dot' : 'signal-dot signal-dot--off'} />{connected ? 'Audit Connected' : 'Setup Pending'}</span>
          <span className="mode-chip"><ShieldCheck aria-hidden="true" />{agentStatus.data?.mode?.toUpperCase() ?? 'SHADOW'} ONLY</span>
        </div>
      </header>

      <aside className="sidebar desktop-sidebar">
        <nav aria-label="Primary navigation">
          {desktopNavigation.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/agent'} className={({ isActive }) => primaryClass(to, isActive)} aria-label={label} title={label}>
              <Icon aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
          <div className="sidebar-group-label"><Archive aria-hidden="true" /><span>Research Archive</span></div>
          {archiveNavigation.map(({ to, label, icon: Icon }) => (
            <NavLink className="archive-nav-link" key={to} to={to} aria-label={label} title={label}>
              <Icon aria-hidden="true" /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="connection-line"><span className={connected ? 'signal-dot' : 'signal-dot signal-dot--off'} />{connected ? 'Public audit ready' : 'Waiting for audit store'}</div>
          <p>PAPER OPTIONS / DEFINED RISK</p>
        </div>
      </aside>

      <div className="workspace">
        {inResearchArchive && (
          <section className="archive-context" aria-labelledby="archive-context-title">
            <div>
              <p className="eyebrow">PRE-HACKATHON RESEARCH / KOREAN MARKET</p>
              <h2 id="archive-context-title">Research Archive</h2>
              <p>Retained provenance—not US agent execution.</p>
            </div>
            <label className="run-select archive-run-select">
              <span>RESEARCH RUN</span>
              <select aria-label="Select Korean research run" value={researchRunId} onChange={(event) => setSelectedResearchRunId(event.target.value)} disabled={!researchRuns.data?.length}>
                {!researchRuns.data?.length && <option value="">No run</option>}
                {researchRuns.data?.map((run) => <option key={run.run_id} value={run.run_id}>{run.run_id}</option>)}
              </select>
            </label>
            <nav aria-label="Research Archive sections">
              {archiveNavigation.map(({ to, label }) => <NavLink key={to} to={to}>{label}</NavLink>)}
            </nav>
          </section>
        )}
        <main id="main-content" tabIndex={-1}>
          <Outlet context={{ runId: researchRunId } satisfies WorkspaceContext} />
        </main>
        <footer className="disclaimer">
          <ShieldCheck aria-hidden="true" /> Alpaca paper trading only. No live mode, naked options, investment advice, or profitability claim.
        </footer>
      </div>

      <nav className="mobile-bottom-nav" aria-label="Mobile navigation">
        {primaryNavigation.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === '/agent'} className={({ isActive }) => primaryClass(to, isActive)}>
            <Icon aria-hidden="true" /><span>{label}</span>
          </NavLink>
        ))}
        <button ref={moreButton} type="button" data-active={moreSectionActive} aria-haspopup="dialog" aria-expanded={moreOpen} aria-controls="mobile-more-sheet" onClick={() => setMoreOpen(true)}>
          <Ellipsis aria-hidden="true" /><span>More</span>
        </button>
      </nav>

      {moreOpen && (
        <>
          <button className="scrim mobile-more-scrim" type="button" aria-label="Close More menu" onClick={closeMore} />
          <div ref={moreSheet} id="mobile-more-sheet" className="mobile-more-sheet" role="dialog" aria-modal="true" aria-labelledby="mobile-more-title">
            <header><div><span className="eyebrow">MORE</span><h2 id="mobile-more-title">Data &amp; Research</h2></div><button className="icon-button" type="button" aria-label="Close More menu" onClick={closeMore}><X aria-hidden="true" /></button></header>
            <nav aria-label="Agent data">
              <NavLink to="/data" onClick={() => setMoreOpen(false)}><Database aria-hidden="true" /><span>Data Health</span></NavLink>
            </nav>
            <p>Pre-hackathon Korean-market research is preserved separately from US agent execution.</p>
            <nav aria-label="Research Archive">
              {archiveNavigation.map(({ to, label, icon: Icon }) => (
                <NavLink key={to} to={to} onClick={() => setMoreOpen(false)}><Icon aria-hidden="true" /><span>{label}</span></NavLink>
              ))}
            </nav>
          </div>
        </>
      )}
    </div>
  )
}
