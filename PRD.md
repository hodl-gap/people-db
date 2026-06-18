# PRD — AI-Trend SNS Monitor (high-level)

## Problem
Keeping up with what AI leaders are doing/thinking means manually scrolling
LinkedIn & X daily. Most of the feed is noise; the signal is scattered and easy
to miss.

## Goal
An agent that **reads LinkedIn + X for me**, surfaces **only the significant
posts** (AI-industry trends — what leaders are building/thinking), and
**likes/follows** the significant ones to tune my feed toward more of that.
Unattended; I just read the digest.

## Users
Me (single-user, personal). Runs on my logged-in browser sessions.

## Principles / key decisions
- **Browser automation (chrome-devtools), not a scraping library** — required so
  it can act (like/follow), not just read.
- **One significance bar:** "what AI leaders are doing/thinking." Everything
  scraped is recorded (dedup); only significant surfaces.
- **Cross-platform identity** via a shared registry (LinkedIn-dead ≠ X-dead).
- Human-paced, personal-use, respects platform ToS.

## In scope
Reading specified people's activity + my home feed; significance filtering;
dated digests; auto like/follow on significant items; a people/entity registry.

## Out of scope (for now)
Posting/replying/DMs; multi-user; real-time; platforms beyond LinkedIn/X;
podcast/video transcription.

## Architecture (lean — the agent does most of the work)

Because an agent drives the browser, most "components" are just prompt
instructions. Only two things need real persistent state.

**Brain**
- **Rubric** (`SIGNIFICANCE.md`) — the SIG/INSIG/SKIP criteria.
- **Judge** — an agent applying the rubric to each (merged) post.

**Persistent state (the only real build-out)**
- **Entity registry** — extend `people-db` to people **+ orgs + projects**
  (Marin, autoresearch, Corca, LETSUR…). The judge looks entities up to resolve
  AI-relevance; also the cross-platform join key.
- **Cross-run dedup store** — a "seen-ids" record the agent reads at the start
  and writes at the end (headless runs have no memory otherwise), so nothing is
  re-reported day to day.

**Agent instructions (prompt directives, not systems)**
- *Scan prompt:* when you hit a thread, **expand it** and capture the whole
  chain as one item.
- *Judge prompt:* **look up entities** in the registry; **follow a link** only
  when the call is otherwise borderline (unreadable link → SKIP); cluster
  **same-topic posts within a run**; apply the **recency** gate.

**Flow**
`scrape → expand threads → judge (rubric + entity lookup + follow link if borderline)
→ dedup (in-run + vs seen-store) → report survivors → like/follow them`

## Status checklist

**Foundations**
- [x] LinkedIn reader (`linkedin-scraper`) — proven
- [x] X reader (`twitter-scraper-chrome-devtools`) — proven
- [x] Auth: shared logged-in Chrome profile (X decoupled-login solved)
- [x] People registry (`people-db`) — seeded
- [x] Significance rubric v1 (`SIGNIFICANCE.md`) + 37-post labeled corpus

**Persistent state**
- [ ] Extend `people-db` → entity registry (people + orgs + projects)
- [ ] Cross-run dedup / seen-ids store

**Brain**
- [ ] Build the judge; validate it reproduces the 37 labels

**Agent instructions (prompt work)**
- [ ] Scan prompt: expand & merge threads
- [ ] Judge prompt: entity lookup · link-follow-if-borderline · in-run topic-dedup · recency

**Engagement (the actual point)**
- [ ] Decide report-worthy vs amplify-worthy (one bar or two)
- [ ] Auto like + follow on significant items (rate caps + logging)

**Operations**
- [ ] Scheduling (cron / routine) for hands-off runs
- [ ] Data gaps: Corca "Alan", Korean founders' X handles, refresh stale statuses

**Quality (ongoing)**
- [ ] Grow the labeled corpus until the filter catches what I *genuinely* want
