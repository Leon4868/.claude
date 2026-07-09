#!/bin/bash
# SessionStart hook: 若可视化服务器未运行则后台拉起，并仅在首次启动时打开浏览器。
PORT=5183
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$ROOT/server.log"

if curl -s -o /dev/null -m 1 "http://localhost:$PORT/state.json"; then
  exit 0
fi

nohup node "$ROOT/server.mjs" "$PORT" >> "$LOG" 2>&1 &
disown

for i in 1 2 3 4 5; do
  sleep 0.3
  if curl -s -o /dev/null -m 1 "http://localhost:$PORT/state.json"; then
    open "http://localhost:$PORT/" >/dev/null 2>&1
    break
  fi
done

exit 0
