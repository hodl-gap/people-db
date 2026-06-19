#!/usr/bin/env python3
"""Resolve YT recommended-video discoveries to their REAL channel via yt-dlp,
then add to channels.json. Defeats impersonators by:
  - resolving the channel from the VIDEO ID (authoritative), never from a
    display name or a synthesized handle;
  - deduping on the canonical channel id (UC...);
  - rejecting channels below a subscriber floor (squatters have ~tens of subs).

Input disc records (one per valid+recent recommended video):
  {"video_id":"...", "title":"...", "age":"...", "channel_name":"...", "kind":"person|organization"}

Usage:
  resolve_and_add_channels.py --channels channels.json --disc vids.jsonl \
      --today 2026-06-19 --min-subs 1000
"""
import argparse, json, os, subprocess

def load_jsonl(path):
    out = []
    if path and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try: out.append(json.loads(line))
                except Exception: pass
    return out

def resolve(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    fmt = "%(channel_id)s\t%(channel)s\t%(channel_follower_count)s\t%(uploader_url)s"
    try:
        r = subprocess.run(["yt-dlp", "--skip-download", "--no-warnings", "--print", fmt, url],
                           capture_output=True, text=True, timeout=90)
        line = (r.stdout or "").strip().splitlines()
        if not line: return None
        parts = (line[0].split("\t") + ["", "", "", ""])[:4]
        cid, name, subs, uurl = parts
        return {
            "channel_id": cid or None,
            "name": name or None,
            "subs": int(subs) if subs.isdigit() else None,
            "handle": (uurl.rstrip("/").split("/")[-1] if uurl else None),
            "url": uurl or None,
        }
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channels", required=True)
    ap.add_argument("--disc", required=True)
    ap.add_argument("--today", required=True)
    ap.add_argument("--min-subs", type=int, default=1000)
    a = ap.parse_args()

    data = json.load(open(a.channels, encoding="utf-8"))
    chans = data["channels"]
    have_ids = {c.get("channel_id") for c in chans if c.get("channel_id")}
    have_handles = {(c.get("channel") or "").lower().lstrip("@").rstrip("/") for c in chans}

    added, rejected, known, unresolved = [], [], [], []
    seen_this_run = set()
    for d in load_jsonl(a.disc):
        vid = d.get("video_id")
        if not vid: continue
        r = resolve(vid)
        if not r or not r["channel_id"]:
            unresolved.append(d.get("title", vid)); continue
        cid = r["channel_id"]
        if cid in seen_this_run: continue
        seen_this_run.add(cid)
        h = (r["handle"] or "").lower().lstrip("@")
        if cid in have_ids or (h and h in have_handles):
            known.append(r["name"] or h); continue
        if r["subs"] is not None and r["subs"] < a.min_subs:
            rejected.append(f"{r['name']} ({r['subs']} subs, via '{d.get('title','')[:40]}')"); continue
        chans.append({
            "channel": r["handle"] or cid,
            "channel_id": cid,
            "url": r["url"] or f"https://www.youtube.com/channel/{cid}",
            "name": r["name"] or r["handle"],
            "kind": d.get("kind", "unknown"),
            "linked_person": None,
            "subscribers": r["subs"],
            "status": "unknown", "last_checked": None,
            "notes": f"Discovered via YT recommended feed {a.today} (recent<=2wk + valid/SIG); resolved from video {vid}.",
        })
        have_ids.add(cid); added.append(f"{r['name']} ({r['subs']} subs)")

    json.dump(data, open(a.channels, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[channels] added: {added or '-'}")
    print(f"[channels] rejected (< {a.min_subs} subs / impersonator): {rejected or '-'}")
    print(f"[channels] already known: {known or '-'}")
    if unresolved: print(f"[channels] could not resolve: {unresolved}")
    print(f"[channels] total: {len(chans)}")

if __name__ == "__main__":
    main()
