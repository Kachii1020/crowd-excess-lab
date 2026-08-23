# Tasks: Crowd Excess Research Workbench

## Dependencies

- T302 depends on T301.
- T304 depends on T302–T303.
- T307 depends on T305–T306.
- T309 depends on T307–T308 and a visual-direction choice.
- T310 depends on all implementation tasks.

## Specification and design discovery

- [x] T301 Define product scope, scenarios, requirements, architecture, data model, HTTP contract,
  and quality checklist under `specs/003-research-workbench/` — covers FR-301–315.
- [x] T302 Install and verify Web Design Guidelines, Image to Code, and Playwright CLI; download the
  Awesome DESIGN.md library and persist candidate comparisons outside app source.
- [x] T303 Generate three product-specific screen references and record the shared design contract.

## US1/US4 — Read-only research API

- [x] T304 Add failing repository/API tests under `tests/api/` for run discovery, exact real-artifact
  projection, path containment, partial stages, event detail, and lineage — covers FR-301–305,
  FR-313, FR-315.
- [x] T305 Implement `src/crowd_excess_lab/api/` and `crowd-excess-api` CLI; expose health, runs,
  events, and lineage contracts — passes T304.

## Shared frontend foundation

- [x] T306 Scaffold `web/` with React/TypeScript/Vite, test/lint/type/build scripts, typed API client,
  query provider, router, and offline fixtures — covers FR-306–307 and FR-313.
- [x] T307 Implement semantic token contracts, density/responsive rules, App Shell, command bar,
  status primitives, blocked/empty/error states, and disclaimer — covers FR-308, FR-310–314.

## US1/US2/US3/US4 — Feature screens

- [x] T308 Implement Overview, Event Monitor, Evidence, Research Matrix, Data Lineage, and Settings
  feature slices with unit tests — covers FR-307–315.
- [x] T309 Apply the selected B-layout/A-palette visual system from `DESIGN.md` and generated
  references without changing research contracts — covers FR-318.
- [x] T311 Convert all user-visible workbench copy and browser metadata to English and make the
  three-pane Event Monitor the primary hackathon screen — covers FR-316–318.

## Cross-cutting verification

- [x] T310 Run Python and frontend tests, lint, type checking, builds, Vercel interface audit,
  Playwright keyboard/responsive/console checks, and reconcile all spec/task evidence.
