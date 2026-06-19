#!/usr/bin/env python3
"""Print the scan watchlist for a platform, derived from people.json (policy D:
watchlist == people-db). One handle/id per line.

Includes people with a usable handle whose status is active | dormant | unknown.
Excludes dead | none | not_found (no point scanning), and null handles.

Usage:  list_watchlist.py --people people.json --platform x
"""
import argparse, json

SCAN_STATUS = {"active", "dormant", "unknown"}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--people", required=True)
    ap.add_argument("--platform", required=True, choices=["x", "linkedin"])
    a = ap.parse_args()
    data = json.load(open(a.people, encoding="utf-8"))
    out = []
    for r in data["people"]:
        pf = r.get("platforms", {}).get(a.platform, {})
        h = pf.get("handle") if a.platform == "x" else pf.get("id")
        if h and pf.get("status", "unknown") in SCAN_STATUS:
            out.append(h)
    print("\n".join(out))

if __name__ == "__main__":
    main()
