#!/bin/bash
# 转写入口：./ingest.sh <小宇宙单集链接>
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ] || [ ! -d models ]; then
  echo "尚未安装，先运行 ./setup.sh" >&2
  exit 1
fi
exec .venv/bin/python ingest.py "$@"
