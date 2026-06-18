# people-db

A small, hand-managed registry of people tracked across social platforms —
the **cross-platform join layer** shared by `linkedin-scraper` and
`twitter-scraper-chrome-devtools` (and the significance filter's
entity-context lookup).

It answers three things per person:
1. **Canonical identity** — one `canonical_name` to join the same person across
   platforms (and `aliases` for other name forms, e.g. Korean / display names).
2. **Their SNS ids** — LinkedIn id and X handle.
3. **Activeness** — per-platform status, so we know where a person actually
   posts (e.g. Karpathy: dead on LinkedIn, active on X).

## Schema (`people.json`)

```jsonc
{
  "canonical_name": "Andrej Karpathy",     // join key (unique)
  "aliases": ["Gyuhyeon Sim", "심규현"],     // other name forms
  "role_org": "Founder, Eureka Labs; ...", // entity-context (also feeds the filter)
  "platforms": {
    "x":        { "handle": "karpathy", "status": "active", "last_checked": "2026-06-18" },
    "linkedin": { "id": "andrej-karpathy-9a650716", "status": "dead", "last_checked": "2026-06-18" }
  },
  "notes": "free text"
}
```

**`status` vocabulary:**
| status | meaning |
|--------|---------|
| `active` | posts regularly + recently |
| `dormant` | has posts but stale (months old) |
| `dead` | account exists, ~no real use (a few very old posts) |
| `none` | account exists but never originates content |
| `not_found` | could not confidently identify the account |
| `unknown` | not yet checked |

`last_checked` (YYYY-MM-DD) is when that platform's status was last verified —
treat older dates as stale.

## How it's used

- **Scrapers** read handles/ids from here to know who to scan and on which
  platform (skip `dead`/`none`, prioritize `active`).
- **Significance filter** uses `role_org` + `canonical_name` as the
  entity-context layer (the labels showed surface text is often opaque without
  knowing who/what is referenced — see `SIGNIFICANCE.md`).
- **Dedup/join** uses `canonical_name` to merge the same person's activity
  across LinkedIn and X.

## Maintenance

Hand-edited JSON. When you verify someone's platform, update `status` +
`last_checked`. Add new people as full records. Keep `canonical_name` unique.

## Seed (2026-06-18)

Seeded from research in this period: 5 X-native AI figures (Karpathy, Pachocki,
Cherny, Dwarkesh, Percy — all dead/dormant on LinkedIn, active on X), the LETSUR
founders (LinkedIn-active, esp. CEO `ghsim`), and Corca's CEO/co-founder.
**Open:** Corca's "CTO Alan" is unresolved; several X handles for the Korean
founders are unknown; LETSUR co-founder statuses are from 2026-06-02 and stale.
