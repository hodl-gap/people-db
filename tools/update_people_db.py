#!/usr/bin/env python3
"""Update people.json from a scan run (the people-db auto-grow step).

- Refreshes status=active / last_checked for people who were scanned and posted.
- Appends newly-discovered PEOPLE (followed third-party authors) as new records.
- Skips organization/product accounts (a denylist + the agent's kind=organization).

Watchlist == people-db, so a newly-added person is scanned on the next run (policy D).
Idempotent: re-running with the same data changes nothing.

Usage:
  update_people_db.py --people people.json --platform x \
      --today 2026-06-19 --raw run.jsonl --disc discoveries.jsonl
"""
import argparse, json, os

# Known org/product accounts that must never enter the human-DB.
ORG_X = {"claudeai", "anthropicai", "openai", "googleai", "googledeepmind",
         "togethercompute", "claudedevs", "perplexity_ai", "huggingface", "ramp"}

def load_jsonl(path):
    out = []
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try: out.append(json.loads(line))
            except Exception: pass
    return out

def plat_key(rec, platform):
    pf = rec.get("platforms", {}).get(platform, {})
    v = pf.get("handle") if platform == "x" else pf.get("id")
    return (v or "").lower().lstrip("@")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--people", required=True)
    ap.add_argument("--platform", required=True, choices=["x", "linkedin"])
    ap.add_argument("--today", required=True)
    ap.add_argument("--raw", default="")
    ap.add_argument("--disc", default="")
    a = ap.parse_args()

    data = json.load(open(a.people, encoding="utf-8"))
    people = data["people"]
    idx = {plat_key(r, a.platform): r for r in people if plat_key(r, a.platform)}
    norm = lambda n: " ".join((n or "").lower().split())
    name_idx = {norm(r.get("canonical_name")): r for r in people if r.get("canonical_name")}

    # 1) refresh: anyone who appears as an author in the raw store was active.
    raw = load_jsonl(a.raw)
    seen_handles = set()
    for post in raw:
        if a.platform == "x":
            h = (post.get("handle") or "").lower().lstrip("@")
        else:
            prof = post.get("profile") or ""
            h = prof.rstrip("/").split("/in/")[-1].lower() if "/in/" in prof else ""
        if h: seen_handles.add(h)
    refreshed = []
    for h in seen_handles:
        if h in idx:
            pf = idx[h]["platforms"][a.platform]
            pf["status"] = "active"; pf["last_checked"] = a.today
            refreshed.append(idx[h]["canonical_name"])

    # 2) discoveries: add new PEOPLE only.
    added, skipped = [], []
    for d in load_jsonl(a.disc):
        if (d.get("platform") or a.platform) != a.platform:
            continue
        handle = (d.get("handle") or d.get("id") or "").lower().lstrip("@").rstrip("/")
        if "/in/" in handle: handle = handle.split("/in/")[-1]
        if not handle: continue
        if d.get("kind") == "organization" or (a.platform == "x" and handle in ORG_X):
            skipped.append(handle); continue
        if handle in idx:
            continue  # already known
        # cross-platform same-person merge: same canonical_name already on file ->
        # fill THIS platform's handle into that record instead of duplicating.
        nm = norm(d.get("name") or "")
        if nm and nm in name_idx:
            ex = name_idx[nm]; pf = ex["platforms"].setdefault(a.platform, {})
            if not (pf.get("handle") or pf.get("id")):
                pf["handle" if a.platform == "x" else "id"] = handle
                pf["status"] = "active"; pf["last_checked"] = a.today
            idx[handle] = ex; added.append(ex["canonical_name"] + " (merged)")
            continue
        rec = {
            "canonical_name": d.get("name") or handle,
            "aliases": [],
            "role_org": d.get("role_org", "") or "(discovered; role TBD)",
            "platforms": {
                "x": {"handle": handle if a.platform == "x" else None,
                      "status": "active" if a.platform == "x" else "unknown",
                      "last_checked": a.today if a.platform == "x" else None},
                "linkedin": {"id": handle if a.platform == "linkedin" else None,
                             "status": "active" if a.platform == "linkedin" else "unknown",
                             "last_checked": a.today if a.platform == "linkedin" else None},
            },
            "notes": d.get("note", f"Auto-discovered via a significant {a.platform} reshare on {a.today}."),
        }
        people.append(rec); idx[handle] = rec
        name_idx[norm(rec["canonical_name"])] = rec; added.append(rec["canonical_name"])

    json.dump(data, open(a.people, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[people-db] refreshed: {refreshed or '-'}")
    print(f"[people-db] added: {added or '-'}  (skipped orgs: {skipped or '-'})")
    print(f"[people-db] total people: {len(people)}")
    if len(people) >= 50:
        print(f"[people-db] ⚠ {len(people)} people — past the ~50 mark; revisit watchlist=people-db policy.")

if __name__ == "__main__":
    main()
