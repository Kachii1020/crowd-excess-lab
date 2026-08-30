# Crowd Excess — Final Video Edit Specification

Status: **frozen for production**

The final video uses the fact-locked English script in `docs/VIDEO_SCRIPT.md`. AI narration is
allowed; a personal voice is not required. The edit must remain truthful to the public production
audit and must not use synthetic trading outcomes.

## Delivery contract

- Duration: `4:00–4:20`, always below five minutes.
- Canvas: `1920×1080`, 16:9, 30 fps.
- Video: H.264 MP4, high profile, progressive scan.
- Audio: AAC, 48 kHz, no clipping, consistent perceived loudness.
- Language: English narration with burned-in English captions.
- Source: production pages and public repository only.
- Privacy: no account identifier, credential, email, notification, or private dashboard.

## Editorial standard

- State the problem and product role within the first eight seconds.
- Keep one idea per shot. Remove cursor wandering, loading waits, repeated scrolling, and dead air.
- Use hard cuts or a dissolve shorter than 250 ms; no decorative transition library.
- Hold evidence-bearing frames long enough to read, normally 4–8 seconds.
- Use 120–140% crops only when a run ID, evidence field, gate, or portfolio fact would otherwise be
  unreadable. Never crop away the production domain while claiming a live trace.
- Keep captions to two lines, within title-safe margins, and away from the UI value being discussed.
- Use no music, or mix it at least 18 dB below narration.
- Do not animate financial numbers or use profit-style green flashes.

## Locked story sequence

1. Product definition and Crowd Excess formula.
2. Fixed universe and honest data boundary.
3. Latest sampled market scan.
4. OpenAI evidence boundary.
5. Deterministic option and risk gates.
6. Failure safety and watchdog.
7. Fact-locked no-order result or exact real receipt branch.
8. Limitation and public links.

## Fact-lock rule

Before the final recording, run:

```bash
uv run --no-sync python scripts/fact_lock.py \
  --require-distinct-market-days 2 \
  --output submission/fact-lock-final.json
```

Every spoken count and financial value must match that file. If `submission_branch` is `no_order`,
use the no-order script without implying execution. If it is `receipt`, replace only the declared
conditional segment and state the exact broker status. Accepted, partial, rejected, canceled, and
filled are different outcomes.

## Frame-level QA

Reject the export if any answer is no:

- Is the product understandable without reading the deck?
- Is the production domain or immutable run ID visible for every claimed real trace?
- Do all counts match `submission/fact-lock-final.json`?
- Are zero P&L and no-order results described without profitability language?
- Is NAVER described as cross-border search attention, never community sentiment?
- Are captions readable at 1280×720 playback?
- Are account identifiers and personal browser surfaces absent from every frame?
- Does the MP4 play from start to finish with synchronized audio?
- Is the total duration below five minutes?

Perform one review with audio and one muted review for visual legibility. Retain the editable source
outside the public repository; commit only the final approved MP4 if repository size permits.
