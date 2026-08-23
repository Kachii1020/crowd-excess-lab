# Crowd Excess Lab — Interface Contract

## Selected direction

Use the information architecture and density of concept B (`Signal Dark`) with the bright,
institutional palette of concept A (`Glass Research`). The product should feel like a calmer,
research-specific Bloomberg workstation rather than a trading terminal.

Primary generated implementation reference:

- `../design-research/crowd-excess-terminal/hybrid-b-layout-a-palette.png`

Supporting research and source notes:

- `../design-research/crowd-excess-terminal/comparison.md`
- Glassnode and Fey candidates for analytical hierarchy and table density.
- Linear and Superhuman candidates for restrained navigation and interaction clarity.

## Product language

- All user-visible product copy is English.
- Use plain research language: `Observed`, `Missing`, `Blocked`, `Pending`, `Evidence`.
- Never use trading actions or claims: no buy, sell, order, position, P&L, alpha, prediction, or
  recommendation language.
- Preserve the disclaimer that outputs are descriptive and in-sample.

## Layout

- Desktop header: 60–64 px, brand left, global command search centered, research mode and run state
  right.
- Desktop navigation: 164–180 px left rail below the header.
- Event Monitor: a flat three-pane workbench.
  - Event table: about 50% of the content width.
  - Attention and fixed-horizon analysis: about 25%.
  - Selected-event evidence: about 25%.
- Provenance rail: full-width strip along the bottom of the workspace with exact source coverage.
- Use one-pixel dividers to create the grid. Avoid nested cards and large rounded wrappers.
- On tablet, move evidence below the table. On mobile, show the event list first and move analysis
  and evidence into a linear read-only flow.

## Color tokens

The implementation should expose semantic variables with approximately this logic:

| Role | Direction |
|---|---|
| Canvas | warm off-white, near `#F5F6F2` |
| Surface | clean white, near `#FFFFFF` |
| Raised surface | quiet cool gray, near `#F7F8F6` |
| Primary text | charcoal, near `#17211C` |
| Secondary text | cool slate, near `#5F6B65` |
| Divider | cool gray-green, near `#DDE3DE` |
| Accent / observed | deep institutional green, near `#187A4A` |
| Accent wash | very pale green, near `#EAF5EE` |
| Pending | muted amber |
| Blocked | muted brick red |
| Focus | accessible blue-green outline distinct from status colors |

Do not use gradients, glassmorphism, glow, neon, or large colored fields.

## Typography

- Use a clean grotesk/system sans for labels and prose.
- Use a monospaced face only for timestamps, run IDs, tickers, hashes, and tabular measurements.
- Page/pane titles: 14–18 px, semibold.
- Table/body copy: 10–12 px on desktop with at least 44 px interactive rows.
- Use sentence case. Reserve uppercase for short technical eyebrows and identifiers.
- All numeric columns use tabular figures and right alignment.

## Components and behavior

- Active navigation uses a pale green wash and a narrow green edge.
- Inputs are rectangular with 2–4 px radii; buttons use the same radius system.
- Status badges are outlined and quiet. Green is evidence of observed/available state, not a
  decorative brand fill.
- Selected table rows use a pale green wash and remain keyboard-focusable.
- Charts must use persisted values only, have axes and units, and include an accessible text
  summary. Missing outcomes render as a labelled pending panel, never as a zero line.
- Evidence shows objective magnitude, attention calculation, missing reasons, and source hashes.
- Provenance shows exact coverage; it never invents completion percentages.

## Motion and accessibility

- Motion is limited to subtle panel/drawer transitions and focus changes.
- Respect `prefers-reduced-motion`.
- Every icon-only action has an accessible name.
- Preserve the skip link, visible focus, sortable column semantics, keyboard search, and mobile
  no-overflow requirement.
