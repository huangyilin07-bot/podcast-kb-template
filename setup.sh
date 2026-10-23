#!/bin/bash
# 安装转写依赖并下载本地语音模型（约 170MB）。可重复执行，已装好的部分会跳过。
# Claude Code 云端会话会自动执行；本机使用（如 Codex）时手动运行一次：./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "缺少 ffmpeg。Mac 请先运行：brew install ffmpeg ；Ubuntu/WSL：sudo apt install ffmpeg" >&2
  exit 1
fi

# 用项目内的虚拟环境，避免和系统 Python 冲突
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/python -m pip install -q --upgrade pip
.venv/bin/python -m pip install -q -r requirements.txt

mkdir -p models && cd models
SV=sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
if [ ! -f "$SV/model.int8.onnx" ]; then
  echo "下载语音模型（约 170MB）…"
  curl -sSfL --retry 3 -o sv.tar.bz2 "$REL/$SV.tar.bz2"
  tar xjf sv.tar.bz2
  rm -rf sv.tar.bz2 "$SV/test_wavs"
fi
[ -f silero_vad.onnx ] || curl -sSfL --retry 3 -o silero_vad.onnx "$REL/silero_vad.onnx"
echo "安装完成。转写命令：./ingest.sh <播客链接>"
