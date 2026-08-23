# Interface Audit — B Layout / A Palette

Reviewed on 2026-08-24 against the current Vercel Web Interface Guidelines and the project
specification after the selected visual system was implemented.

- Pass: semantic page landmarks, skip link, labelled navigation, visible focus, and keyboard search.
- Pass: sortable table state is exposed on column headers; links and icon-only controls have names.
- Pass: no gradients, decorative hero copy, mock return values, order actions, or credential inputs.
- Pass: numeric values use tabular figures; KRW source integers remain exact decimal strings.
- Pass: missing price/index observations stay labelled `Missing` with an explicit reason.
- Pass: charts include a textual observation/missingness summary.
- Pass: event selection, filters, research horizon, and lineage provider state are URL-persisted.
- Pass: form controls have labels, names, explicit light-theme colors, and appropriate autocomplete
  behavior; compound search controls expose focus-within feedback.
- Pass: desktop 1536×1024, automated 1440×900, and mobile 390×844 browser checks; mobile has no
  page-level horizontal overflow.
- Pass: reduced-motion rules disable the sidebar transition and loader animation.
- Pass: browser interaction checks reported no application console errors.

The final system uses concept B's dense three-pane terminal structure with concept A's warm white,
charcoal, and restrained green palette. Exact tokens and responsive behavior are recorded in the
repository `DESIGN.md`; generated and implemented comparison captures live under
`outputs/design-research/crowd-excess-terminal/`.
