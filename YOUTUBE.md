# YouTube source — design

YouTube as a source, treated as **long-form**. Same goal as the rest (catch up on
AI advancements — what leaders are doing/thinking), different shape.

## Two axes (the crux)
- **Output / presentation = the video.** One per-video block: title · participants · AI-focused summary.
- **Storage / identity = the person.** Each *appearing* person becomes/updates a `people.json` record.
- One video → N human records. The video is how a human reads it; the person is how the system stores + joins it.

## Capture — hybrid (use the best tool per part)
- **Content from a known video/channel → `yt-dlp` transcript** (deterministic, cheap, full transcript). NOTE: YT now token-gates the caption endpoint *and* the on-page transcript panel — naive browser/`fetch` returns empty. `yt-dlp --write-auto-subs --skip-download` works (handles signatures); clean the VTT to text. So the transcript adapter is **yt-dlp, not the browser**.
- **Recommended / home feed → logged-in browser only** (no API exposes personalized recommendations).
- **Engagement (like / subscribe / watch) → logged-in browser. DEFERRED.**

## Recommended-feed discovery (built: `youtube-scraper/discover-youtube.sh`)
Grows `channels.json` from the recommended feed. A recommended video's **channel**
is added only when the video passes BOTH strict gates:
1. **Recency** — published within the last **2 weeks** (≤14 days); older is skipped
   no matter how relevant.
2. **Validity** — judged **SIG** by the shared rubric (title + channel +
   entity-context; no transcript).
Discovery only — does not watch/transcribe/like/subscribe. Adds the *channel*
(source), not people.

The judge, rubric, people-db, dedup, discovery, and digest are shared with X/LinkedIn — only the capture adapter differs.

## Two modes
- **v1 — on-demand per-URL.** You hand it a video URL → transcript → AI-focused summary → append participants. No channels list needed.
- **v2 — auto.** `channels.json` (sources) → detect each channel's *new* uploads (incremental, dedup by video id) → AI pre-filter → process the survivors.

## AI pre-filter (before transcribing — transcripts are expensive)
```
new video → cheap gate (title + description + entity-context): AI-relevant?
   ├─ no  → skip, record the id (dedup), never transcribe
   └─ yes → transcript → AI-focused summary → judge → per-video output → append people
```
The gate uses entity-context: a video is AI-relevant if the title/desc says so, **or** the channel is a known AI source, **or** a named guest is a known AI person (people-db) — so AI videos with opaque titles (e.g. just a guest's name) aren't missed.

## Attribution
- The video's **substance → the speaker(s)** (the AI subjects — "what they're doing").
- The **host / channel → source** (credited as "via <channel>", not the owner of the summary).
- Output always credits the channel (person or org); storage only stores humans.

## people-db append rule
- Append **guests/speakers only**. Recurring co-hosts/panelists (e.g. the All-In four) are NOT appended every video — treat a known panel as part of the org-source; only *guests* grow the human-DB.
- **Skip mentioned-only** people (referenced in third person) — the YT analog of "@-mention = ignore."
- **Skip org/brand channels** (Bloomberg Originals, a16z, TED) — not humans (same as denylisting `@OpenAI`).
- `youtube` field on a record = **the host's channel only** (speakers appear on others' channels, so they get no YT field — just X/LinkedIn if resolved).

## SNS resolution on appearing guests
- For each appearing person, try to resolve their other SNS (X/LinkedIn) by **name + corroborating role/affiliation** from the video.
- **Confident-only**: corroborated match → store the handle; otherwise leave `unfound` (never guess — a wrong handle would make us scan/like/follow the wrong person).
- A confidently-resolved handle joins the watchlist (policy D) → that person is then monitored on X/LinkedIn. **YouTube is thus a discovery funnel into the other sources.**

## Registries (two, separate)
- **`people.json`** — humans only; cross-platform identity. Gains a `youtube` field (host channels).
- **`channels.json`** — YouTube sources (the v2 watchlist). A channel is `kind: person|org`; person-channels link to their `people.json` record via `linked_person`. Org channels live here only (never in people-db).

## Engagement (YT)
- Same one bar: a **SIG** video → **like + subscribe** (to the channel), per the dry-run-first → auto rollout. (Optionally "watch"/"not interested" as stronger feed signals — later.)

## Open / later
- A separate sources registry for *org* channels you want auto-scanned (Bloomberg etc.) — only needed once v2 auto-scans org channels.
- Long transcript handling in the judge = "summarize-then-judge" (the unit is a talk, not a one-liner).
