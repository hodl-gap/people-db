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
Posting/replying/DMs; multi-user; real-time; platforms beyond X / LinkedIn /
YouTube.

## Sources (X, LinkedIn, YouTube)

Capture is a **pluggable adapter per platform**; everything downstream (judge,
people-db, dedup, per-person digest, discovery) is shared. So adapters can differ
without breaking human-comprehension consistency — the consistency that matters is
the *interface and output*, not the capture mechanism.

| | watchlist (what's scanned) | capture | unit |
|---|---|---|---|
| **X** | people-db (humans) — policy D | logged-in browser | person's post-stream |
| **LinkedIn** | people-db (humans) — policy D | logged-in browser | person's post-stream |
| **YouTube** | `channels.json` (sources: person- *and* org-channels) | API + transcript (content), browser (recommended feed + engagement) | **the video** |

Two registries, deliberately separate:
- **`people.json`** — humans only; the cross-platform identity/join layer.
- **`channels.json`** — YouTube sources (a channel may be a person *or* an org like
  Bloomberg Originals; orgs are sources but never enter the human-db).

**YouTube specifics** (full spec in `YOUTUBE.md`):
- **Output = per-video; storage = per-person.** One video fans out into N human records.
- Substance attributed to **speaker(s)**; **host/channel = source** (credited, not owner).
- **people-db append = people who *appear*** (person-host + speakers); *mentioned-only*
  people are skipped; **org channels skipped**. `youtube` field = the host's channel only.
- On an appearing guest, **resolve their SNS confident-only** (else `unfound`); a
  resolved handle joins the watchlist (policy D) and is monitored on X/LinkedIn — so
  YT is a discovery funnel into the other sources.
- **Cheap AI pre-filter** (title/desc + entity-context) before pulling a transcript;
  non-AI videos are skipped (recorded for dedup), never transcribed.
- Modes: **v1 on-demand per-URL** (no channels list needed) → **v2 auto** (channels.json
  → detect new uploads → pre-filter → process).

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

**Foundations** — done
- [x] X + LinkedIn readers (browser via chrome-devtools); auth incl. X decoupled-login
- [x] `people-db` seeded; rubric (`judge_prompt.md`) canonical here
- [x] Significance rubric v1 + 37-post labeled corpus; judge validated (100% in-sample)

**M1 — filtered digest** — done (both platforms, verified live)
- [x] CAPTURE (incremental + thread-expand) → JUDGE (rubric + entity-context) → raw store → per-person digest

**M2 — engagement** — built; dry-run verified both platforms; **live not flipped**
- [x] One bar: SIG → like + follow (incl. reshared original author); caps, action log, idempotency
- [ ] Flip to live (one confirming run; verify already-following skip)

**Policy D — watchlist = people-db** — done
- [x] Watchlist derived from people-db; discovery auto-grows people-db each run

**YouTube** — specced (`YOUTUBE.md`); not built
- [ ] v1 on-demand per-URL: transcript → AI pre-filter → per-video summary → append people-host+speakers (confident SNS resolve, orgs skipped)
- [ ] v2 auto: `channels.json` → detect new uploads → pre-filter → process
- [ ] Engagement: like + subscribe on SIG

**Operations**
- [ ] Scheduling (cron / routine) for hands-off runs
- [ ] Data gaps: Corca "Alan", Korean founders' X handles, refresh stale statuses
- [ ] people-db auto-grow is working-copy only — periodic commit / or auto-commit

**Quality (ongoing)**
- [ ] Held-out eval batch (current 100% is in-sample); grow the labeled corpus
