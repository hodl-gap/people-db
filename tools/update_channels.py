#!/usr/bin/env python3
"""Add discovered YouTube channels to channels.json (idempotent).

Fed by the YT recommended-feed discovery: a channel is added only when one of its
videos passed BOTH gates (<=2 weeks old AND valid=SIG). Dedupes against existing.

Usage: update_channels.py --channels channels.json --disc discoveries.jsonl --today 2026-06-19
"""
import argparse, json, os

def load_jsonl(path):
    out = []
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try: out.append(json.loads(line))
                except Exception: pass
    return out

def norm(c): return (c or "").strip().lower().lstrip("@").rstrip("/")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", required=True)
    ap.add_argument("--disc", required=True)
    ap.add_argument("--today", required=True)
    a = ap.parse_args()
    data = json.load(open(a.channels, encoding="utf-8"))
    chans = data["channels"]
    have = {norm(c.get("channel")) for c in chans}
    added = []
    for d in load_jsonl(a.disc):
        ch = d.get("channel") or d.get("id")
        if not ch or norm(ch) in have:
            continue
        chans.append({
            "channel": ch,
            "url": d.get("url", f"https://www.youtube.com/{ch}"),
            "name": d.get("name") or ch,
            "kind": d.get("kind", "unknown"),
            "linked_person": d.get("linked_person"),
            "status": "unknown",
            "last_checked": None,
            "notes": d.get("note", f"Discovered via YT recommended feed {a.today} (recent <=2wk + valid/SIG).")
        })
        have.add(norm(ch)); added.append(ch)
    json.dump(data, open(a.channels, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[channels] added: {added or '-'} | total: {len(chans)}")

if __name__ == "__main__":
    main()
