#!/usr/bin/env bash
#
# yt_transcript.sh <video_id> [out_file]
#
# Fetches a YouTube video's transcript via yt-dlp (auto-subs; YT token-gates the
# naive caption endpoint, yt-dlp handles it) and emits clean plain text — rolling
# caption duplicates removed. Prints to stdout, or saves to out_file if given.
# Exit 2 if no transcript is available.
#
# Shared by discover-youtube.sh (validity gate) and the v1 summarizer.
#
set -euo pipefail
VID="${1:?usage: yt_transcript.sh <video_id> [out_file]}"
OUT="${2:-}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

yt-dlp --skip-download --write-auto-subs --write-subs --sub-langs 'en.*,en' \
  --sub-format vtt -o "$TMP/%(id)s.%(ext)s" \
  "https://www.youtube.com/watch?v=$VID" >/dev/null 2>&1 || true

VTT="$(ls "$TMP"/*.vtt 2>/dev/null | head -1 || true)"
[[ -n "$VTT" ]] || { echo "NO_TRANSCRIPT for $VID" >&2; exit 2; }

TEXT="$(python3 - "$VTT" <<'PY'
import re, sys
lines=[]
for ln in open(sys.argv[1], encoding="utf-8"):
    ln=ln.rstrip("\n")
    if ln.startswith("WEBVTT") or "-->" in ln or not ln.strip() or ln.startswith(("Kind:","Language:")):
        continue
    ln=re.sub(r"<[^>]+>","",ln).replace("&nbsp;"," ").strip()
    if ln: lines.append(ln)
out=[]
for ln in lines:                      # drop consecutive rolling-caption repeats
    if not out or out[-1]!=ln: out.append(ln)
print(re.sub(r"\s+"," "," ".join(out)).strip())
PY
)"

if [[ -n "$OUT" ]]; then
  printf '%s' "$TEXT" > "$OUT"
  echo "saved ${#TEXT} chars to $OUT"
else
  printf '%s\n' "$TEXT"
fi
