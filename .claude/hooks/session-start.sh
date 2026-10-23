#!/bin/bash
# Claude Code 云端会话启动时自动安装（本机使用请手动运行 ./setup.sh）。
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
"$CLAUDE_PROJECT_DIR/setup.sh"
