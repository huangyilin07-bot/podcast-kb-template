#!/bin/bash
# 云会话启动时安装转写依赖并下载本地语音模型（约 170MB）。可重复执行。
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"
pip install -q -r requirements.txt

mkdir -p models && cd models
SV=sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09
REL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models
if [ ! -f "$SV/model.int8.onnx" ]; then
  curl -sSfL --retry 3 -o sv.tar.bz2 "$REL/$SV.tar.bz2"
  tar xjf sv.tar.bz2
  rm -rf sv.tar.bz2 "$SV/test_wavs"
fi
[ -f silero_vad.onnx ] || curl -sSfL --retry 3 -o silero_vad.onnx "$REL/silero_vad.onnx"
