import { Component, type ErrorInfo, type ReactNode } from 'react'

type State = { error: Error | null }

export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Workbench render failure', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <main className="fatal-state">
          <p className="eyebrow">CROWD EXCESS / RECOVERY</p>
          <h1>The workbench could not recover</h1>
          <p>{this.state.error.message}</p>
          <button className="button" type="button" onClick={() => window.location.reload()}>Reload</button>
        </main>
      )
    }
    return this.props.children
  }
}
