import {
  BrainCircuit, CheckCircle2, CircleDashed, Clock3, Database,
  ExternalLink, Gauge, Search, TriangleAlert,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAgentRun, useAgentRuns, useAgentStatus, useStrategy } from '../api/queries.ts'
import type { AgentRunDetail } from '../api/schemas.ts'
import { ErrorState, LoadingState } from '../components/States.tsx'
import { StatusBadge } from '../components/StatusBadge.tsx'
import { healthState, type HealthState } from '../lib/dataHealth.ts'
import { format } from '../lib/format.ts'

type HealthItem = {
  name: string
  state: HealthState
  cause: string
  observedAt: string | null
  explanation: string
  icon: typeof Database
}

const sourcePrefixes = {
  naver: 'naver_',
  market: 'alpaca_market_',
  options: 'alpaca_options_',
  openai: 'openai_evidence_',
}

function hasSource(detail: AgentRunDetail | undefined, prefix: string) {
  return Object.keys(detail?.run.source_hashes ?? {}).some((key) => key.startsWith(prefix))
}


function stateKey(state: HealthState) {
  return state.toLowerCase().replace(' ', '_')
}

export function DataHealthPage() {
  const status = useAgentStatus()
  const runs = useAgentRuns()
  const strategy = useStrategy()
  const latestRun = status.data?.last_run ?? runs.data?.[0]
  const detail = useAgentRun(latestRun?.run_id ?? '')

  if (status.isLoading || runs.isLoading || strategy.isLoading || detail.isLoading) {
    return <LoadingState label="Loading data health" />
  }
  if (status.error || runs.error || strategy.error || detail.error) {
    const auditError = status.error ?? runs.error ?? detail.error
    if (!auditError) return <ErrorState error={strategy.error ?? new Error('Strategy configuration is unavailable.')} retry={() => window.location.reload()} />
  }

  const run = detail.data?.run ?? latestRun
  const signals = detail.data?.signals ?? []
  const clock = run?.market_clock
  const runObservedAt = clock?.observed_at ?? run?.completed_at ?? run?.started_at ?? null
  const latestSignalAt = signals.reduce<string | null>((latest, signal) => {
    if (!latest || new Date(signal.source_as_of) > new Date(latest)) return signal.source_as_of
    return latest
  }, null)
  const runText = `${run?.summary ?? ''} ${run?.error ?? ''}`.toLowerCase()
  const closed = clock ? !clock.is_open : /(market.*closed|outside.*market|outside.*window|market window)/.test(runText)
  const naverSampled = hasSource(detail.data, sourcePrefixes.naver)
  const marketSampled = hasSource(detail.data, sourcePrefixes.market)
  const optionsSampled = hasSource(detail.data, sourcePrefixes.options)
  const openaiSampled = hasSource(detail.data, sourcePrefixes.openai)
  const evidenceFailed = signals.some((signal) => signal.evidence.abstention_reason === 'openai_evidence_unavailable')
  const riskSampled = Boolean(detail.data?.risk_decision)
  const auditUnavailable = Boolean(status.error || runs.error || detail.error)
  const failureStage = run?.failure_stage ?? null
  const failureCode = run?.failure_code ?? null
  const optionBoundaryFailure = failureCode === 'alpaca_option_chain_unavailable'
    || failureCode === 'alpaca_option_volume_unavailable'
  const riskBoundaryFailure = failureCode === 'risk_evaluation_unavailable'
  const boundaryDiagnostic = failureStage && failureCode
    ? `Stage ${failureStage.replaceAll('_', ' ')} · code ${failureCode}`
    : null

  const items: HealthItem[] = [
    {
      name: 'NAVER Attention',
      state: healthState(naverSampled, latestSignalAt ?? runObservedAt, false),
      cause: naverSampled ? `${signals.length} symbol observations are attached to the latest trace.` : closed ? 'The latest run ended before provider sampling.' : 'No NAVER source hash exists on the latest run.',
      observedAt: naverSampled ? latestSignalAt ?? runObservedAt : runObservedAt,
      explanation: 'Daily relative search attention is contextual evidence, not community sentiment. Missing observations are never treated as zero.',
      icon: Search,
    },
    {
      name: 'Alpaca Market',
      state: healthState(marketSampled, latestSignalAt ?? runObservedAt, false),
      cause: marketSampled ? 'Underlying, SPY, and volume observations were recorded.' : closed ? `The latest market clock observation was closed${clock?.next_open ? `; next open was reported as ${format.dateTime(clock.next_open)}` : ''}.` : 'No Alpaca market source hash exists on the latest run.',
      observedAt: marketSampled ? latestSignalAt ?? runObservedAt : runObservedAt,
      explanation: `Market observations older than ${strategy.data?.max_market_data_age_seconds ?? 120} seconds cannot pass execution gates. A stored snapshot describes that run, not the market now.`,
      icon: Clock3,
    },
    {
      name: 'Alpaca Options',
      state: healthState(optionsSampled, runObservedAt, optionBoundaryFailure),
      cause: failureStage?.startsWith('option_') && failureCode
        ? `Candidate stopped at ${failureStage.replaceAll('_', ' ')} (${failureCode}); raw provider details were not retained.`
        : optionsSampled ? 'The selected option chain and its source hash were recorded.' : marketSampled ? 'No signal reached option-chain construction in the latest run.' : 'The run ended before option-chain sampling could be considered.',
      observedAt: optionsSampled ? runObservedAt : null,
      explanation: 'Option chains are requested only after a signal is eligible. Not sampled is a safe stage outcome, not a missing quote represented as zero.',
      icon: Gauge,
    },
    {
      name: 'OpenAI Evidence',
      state: healthState(openaiSampled, runObservedAt, evidenceFailed),
      cause: openaiSampled ? 'Strict evidence assessments and their input hashes were recorded.' : evidenceFailed ? 'Structured evidence assessment was unavailable; the affected signal abstained.' : 'No eligible market evidence reached model assessment in this run.',
      observedAt: openaiSampled || evidenceFailed ? runObservedAt : null,
      explanation: 'The model scores supplied headlines only. Invalid, refused, or timed-out responses become ABSTAIN and cannot select an order.',
      icon: BrainCircuit,
    },
    {
      name: 'Risk Engine',
      state: healthState(riskSampled, detail.data?.risk_decision?.evaluated_at ?? runObservedAt, riskBoundaryFailure),
      cause: failureStage === 'risk_evaluation' && failureCode
        ? `Candidate stopped at risk evaluation (${failureCode}).`
        : riskSampled ? `${detail.data?.risk_decision?.gates.length ?? 0} deterministic gates were recorded.` : 'No candidate reached option-structure risk evaluation in this run.',
      observedAt: riskSampled ? detail.data?.risk_decision?.evaluated_at ?? runObservedAt : null,
      explanation: 'A missing risk decision means no execution approval. It does not mean the gates passed.',
      icon: Gauge,
    },
    {
      name: 'Audit Store',
      state: auditUnavailable || !status.data?.configured ? 'Error' : healthState(Boolean(run), runObservedAt, false),
      cause: auditUnavailable ? 'The public audit API could not be read.' : status.data?.configured ? run ? 'Append-only public records are readable.' : 'The store is connected but no agent run is recorded yet.' : 'Public audit storage is not configured.',
      observedAt: runObservedAt,
      explanation: 'The public application is read-only. Write credentials and order controls are not delivered to the browser.',
      icon: Database,
    },
  ]

  const summary = items.reduce<Record<HealthState, number>>((counts, item) => {
    counts[item.state] += 1
    return counts
  }, { Ready: 0, 'Not sampled': 0, Stale: 0, Error: 0 })

  return (
    <div className="page data-health-page">
      <header className="data-health-hero">
        <div><p className="eyebrow">LATEST RECORDED OBSERVATIONS</p><h1>Data Health</h1><p>Provider readiness for the latest autonomous check—without converting missing or unsampled data into a green status.</p></div>
        <div className="health-summary" aria-label="Data health summary" aria-live="polite">
          {(Object.entries(summary) as [HealthState, number][]).map(([state, count]) => <span key={state}><strong>{count}</strong> {state}</span>)}
        </div>
      </header>

      {auditUnavailable && (
        <section className="data-health-alert" role="alert"><TriangleAlert aria-hidden="true" /><div><h2>Audit API unavailable</h2><p>Source history cannot be verified right now. Strategy documentation remains available, but no provider is assumed healthy.</p></div></section>
      )}

      {boundaryDiagnostic && (
        <section className="data-health-alert" role="status"><CircleDashed aria-hidden="true" /><div><h2>Latest boundary outcome</h2><p>{boundaryDiagnostic}. The public trace stores only this sanitized diagnostic.</p></div></section>
      )}

      <section className="health-detail-list" aria-label="Provider health">
        {items.map(({ name, state, cause, observedAt, explanation, icon: Icon }) => (
          <article key={name} className="panel health-detail" data-state={stateKey(state).replace('_', '-')}>
            <header><span className="health-detail-icon"><Icon aria-hidden="true" /></span><div><h2>{name}</h2><StatusBadge status={stateKey(state)}>{state}</StatusBadge></div></header>
            <dl><div><dt>Why this status</dt><dd>{cause}</dd></div><div><dt>Last observed</dt><dd>{observedAt ? format.dateTime(observedAt) : 'Not observed'}</dd></div></dl>
            <p>{explanation}</p>
            <span className="health-state-cue" aria-hidden="true">{state === 'Ready' ? <CheckCircle2 /> : state === 'Error' ? <TriangleAlert /> : <CircleDashed />}</span>
          </article>
        ))}
      </section>

      <section className="data-boundary-callout">
        <div><p className="eyebrow">DATA BOUNDARY</p><h2>US execution and Korean research stay separate</h2><p>NAVER search ratios are one cross-border attention input. The OpenDART/KRX event study remains pre-hackathon research provenance.</p></div>
        <Link className="button" to="/research">Open Research Archive <ExternalLink aria-hidden="true" /></Link>
      </section>
    </div>
  )
}
