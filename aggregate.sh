#!/usr/bin/env bash
#
# aggregate.sh — daily brief that merges the day's significant items from the X /
# LinkedIn / YouTube scrapers into ONE report. Browser-less: a small claude -p that
# only reads files + writes the brief (runs AFTER the 3 scans).
#
# It is a BLUNT "who said what" roll-up with coverage counts — NOT a synthesized
# summary. (The aggregator's prompt is authored in Korean.)
#
# Usage:  ./aggregate.sh [YYYY-MM-DD]     # default: today
#
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"
DATE="${1:-$(date +%Y-%m-%d)}"
PEOPLE_DB="$DIR/people.json"
CHANNELS="$DIR/channels.json"
BRIEF_DIR="$DIR/briefs"; mkdir -p "$BRIEF_DIR"
ITEMS="$BRIEF_DIR/.items-$DATE.jsonl"
BRIEF="$BRIEF_DIR/brief-$DATE.md"

# Recency cutoff for X/LinkedIn (fast-moving SNS): drop items PUBLISHED more than
# RECENCY_DAYS before the brief date so first-scan back-catalog doesn't leak in.
# YouTube is EXEMPT here — it has its own <=14d recency gate at capture/discovery.
RECENCY_DAYS="${RECENCY_DAYS:-7}"
CUTOFF="$(python3 -c "import datetime;print((datetime.date.fromisoformat('$DATE')-datetime.timedelta(days=$RECENCY_DAYS)).isoformat())")"

# --- collect the brief-date's SIG/VALUABLE items (scraped that day, published within RECENCY_DAYS) ---
python3 - "$DATE" "$CUTOFF" "$ITEMS" \
  "$DIR/../twitter-scraper-chrome-devtools/store/raw" \
  "$DIR/../linkedin-scraper/store/raw" \
  "$DIR/../youtube-scraper/store/raw" <<'PY'
import sys, glob, json, os
date, cutoff, out = sys.argv[1], sys.argv[2], sys.argv[3]
dirs = sys.argv[4:]
keep = {"SIG", "VALUABLE"}
rows, dropped_old = [], 0
for d in dirs:
    for fp in glob.glob(os.path.join(d, "*.jsonl")):
        if os.path.basename(fp).startswith("."): continue
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try: o = json.loads(line)
            except Exception: continue
            if o.get("label") not in keep: continue
            if not str(o.get("scraped_at", "")).startswith(date): continue
            pub = str(o.get("date") or "")[:10]      # ISO YYYY-MM-DD when present
            # 7d recency applies to fast-moving SNS only; YouTube keeps its own gate
            if o.get("platform") in ("x", "linkedin") and len(pub) == 10 and pub < cutoff:
                dropped_old += 1; continue
            rows.append({
                "platform": o.get("platform", ""),
                "author": o.get("author") or o.get("channel") or "",
                "handle": o.get("handle") or o.get("profile") or o.get("channel") or "",
                "date": o.get("date"),
                "text": (o.get("text") or o.get("title") or "")[:600],
                "source": o.get("id", ""),
            })
with open(out, "w", encoding="utf-8") as f:
    for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"{len(rows)} significant items for {date} (dropped {dropped_old} published before {cutoff})")
PY

NITEMS=$(grep -c . "$ITEMS" 2>/dev/null || echo 0)
NPEOPLE=$(python3 -c "import json;p=json.load(open('$PEOPLE_DB'))['people'];print(sum(1 for r in p if any((r['platforms'].get(k) or {}).get('handle') or (r['platforms'].get(k) or {}).get('id') for k in ('x','linkedin','youtube'))))")
NCH=$(python3 -c "import json;print(len(json.load(open('$CHANNELS'))['channels']))")
echo ">> $DATE: $NITEMS significant items | tracked: $NPEOPLE people, $NCH channels -> $BRIEF"

PROMPT=$(cat <<EOF
당신은 오늘 수집된 'AI 주요 인물들의 유의미한 활동'을 한곳에 모아 정리하는 집계자다.

입력 파일:
- 오늘 X·LinkedIn·YouTube에서 수집된 유의미 항목들의 JSONL: $ITEMS
  (각 줄 필드: platform, author, handle, text, source)
- 추적 대상 인물 레지스트리(같은 인물을 플랫폼 간 연결하는 canonical_name 포함): $PEOPLE_DB
- 오늘 추적 대상 규모: 인물 ${NPEOPLE}명, 채널 ${NCH}개

반드시 지킬 것:
- 전체를 아우르는 한 줄 요약·총평·주제 묶음·해석·전망은 절대 만들지 마라.
  그저 '누가 무엇을 말했는지'를 담백하고 사실 그대로 옮겨라. 윤색·논평·추측 금지.
- 인물 단위로 묶어라. 같은 사람이 여러 플랫폼에 나오면 $PEOPLE_DB 의 canonical_name 으로
  합치고, 각 항목 앞에 플랫폼을 표기하라. 동일 내용이 여러 플랫폼에 중복되면 한 번만 적고
  '(X·YouTube)'처럼 함께 표기하라.
- YouTube 영상은 채널이 아니라 사람에 귀속시켜라: 영상 제목·출연자에 추적 인물
  ($PEOPLE_DB 의 canonical_name/aliases)이 주인공·출연자로 등장하면, 그 인물 섹션 아래에
  '(YouTube) ...'로 붙여 다른 플랫폼 항목과 통합하라(한 영상에 여러 추적 인물이 나오면
  각자 밑에 적되 같은 영상임이 드러나게). 어떤 추적 인물도 중심이 아닐 때(진행자만 나오는
  패널, 비추적 인물 영상)에만 마지막에 '## <채널명> (YouTube 채널)' 섹션으로 따로 둔다.
- 오늘 유의미한 활동이 있은 대상만 실어라. 각 항목은 그가 실제로 말하거나 올린 핵심을
  한두 줄로 짧게, 사실 그대로 적어라.
- source·id 같은 내부 식별자는 최종 결과에 절대 노출하지 마라. 그것은 뒷단 데이터일 뿐이다.
  결과 문장 끝에 식별자나 "author:date:..." 형태의 키를 붙이지 마라.

결과를 마크다운으로 "$BRIEF" 파일에 저장하라. 형식:

# 데일리 브리프 — $DATE
커버리지: 추적 인물 ${NPEOPLE}명 중 N명 활동 · 채널 ${NCH}개 중 M개 활동

## <이름> (<소속/역할 — $PEOPLE_DB 의 role_org 참고>)
- (<플랫폼>) <그가 말하거나 올린 내용, 사실 그대로 짧게>
- ...

(마지막에, 오늘 조용했던 주요 추적 대상이 있으면 "조용함:" 한 줄로 이름만 나열. 그 외 어떤 총평도 쓰지 마라.)

만약 $ITEMS 가 비어 있으면, 커버리지 줄에 "오늘 유의미한 활동 없음"만 적어라.
EOF
)

claude -p "$PROMPT" --permission-mode bypassPermissions --allowedTools "Read,Write" 2>&1 | tee "$BRIEF_DIR/run-$DATE.log"
echo ">> Done. Brief: $BRIEF"
