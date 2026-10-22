"""小宇宙单集 → 元数据 + 音频 + 带时间戳逐字稿。

用法: python3 ingest.py <小宇宙单集链接> [输出目录]
输出: <输出目录>/<eid>/meta.json, audio.m4a, transcript.txt
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

import numpy as np
import sherpa_onnx

MODEL_DIR = os.environ.get(
    "SV_MODEL_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "models"),
)
SV = os.path.join(MODEL_DIR, "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09")
SR = 16000
UA = {"User-Agent": "Mozilla/5.0"}


def fetch_meta(url):
    eid = re.search(r"episode/([0-9a-f]{24})", url).group(1)
    req = urllib.request.Request(f"https://www.xiaoyuzhoufm.com/episode/{eid}", headers=UA)
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    data = json.loads(
        re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S).group(1)
    )
    e = data["props"]["pageProps"]["episode"]
    return {
        "eid": eid,
        "url": f"https://www.xiaoyuzhoufm.com/episode/{eid}",
        "title": e["title"],
        "podcast": e["podcast"]["title"],
        "author": e["podcast"].get("author"),
        "pub_date": e["pubDate"][:10],
        "duration_min": round(e["duration"] / 60),
        "audio_url": (e.get("media") or {}).get("url") or e["enclosure"]["url"],
        "description": e.get("description") or "",
    }


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return
    head = urllib.request.Request(url, headers=UA, method="HEAD")
    total = int(urllib.request.urlopen(head, timeout=30).headers["Content-Length"])
    part = path + ".part"
    # 连接可能被中途切断，按已下载字节续传，直到大小与服务器一致
    for attempt in range(20):
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if have >= total:
            break
        req = urllib.request.Request(url, headers={**UA, "Range": f"bytes={have}-"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r, open(part, "ab") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
        except OSError as err:
            print(f"下载中断（{have}/{total}），重试：{err}", flush=True)
            time.sleep(2)
    if os.path.getsize(part) != total:
        raise RuntimeError(f"音频下载不完整：{os.path.getsize(part)}/{total} 字节")
    os.rename(part, path)


def load_pcm(path):
    raw = subprocess.run(
        ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", path,
         "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def ts(sec):
    sec = int(sec)
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def transcribe(audio_path, out_path):
    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=os.path.join(SV, "model.int8.onnx"),
        tokens=os.path.join(SV, "tokens.txt"),
        num_threads=os.cpu_count() or 4,
        use_itn=True,
        language="auto",
    )
    vcfg = sherpa_onnx.VadModelConfig()
    vcfg.silero_vad.model = os.path.join(MODEL_DIR, "silero_vad.onnx")
    vcfg.silero_vad.min_silence_duration = 0.4
    vcfg.silero_vad.max_speech_duration = 20
    vcfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(vcfg, buffer_size_in_seconds=60)

    samples = load_pcm(audio_path)
    win = vcfg.silero_vad.window_size
    segs = []

    def drain():
        while not vad.empty():
            s = vad.front
            st = rec.create_stream()
            st.accept_waveform(SR, s.samples)
            rec.decode_stream(st)
            text = st.result.text.strip()
            if text:
                segs.append((s.start / SR, text))
            vad.pop()

    t0 = time.time()
    for i in range(0, len(samples), win):
        vad.accept_waveform(samples[i:i + win])
        drain()
    vad.flush()
    drain()

    # 约每 60 秒合并成一段，段首标时间戳，便于回听定位
    lines, buf, start = [], [], None
    for t, text in segs:
        if start is None:
            start = t
        buf.append(text)
        if t - start >= 60:
            lines.append(f"[{ts(start)}] " + "".join(buf))
            buf, start = [], None
    if buf:
        lines.append(f"[{ts(start)}] " + "".join(buf))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(lines) + "\n")
    return time.time() - t0, len(samples) / SR


def main():
    url = sys.argv[1]
    root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "episodes")
    meta = fetch_meta(url)
    d = os.path.join(root, meta["eid"])
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"{meta['podcast']} | {meta['title']} | {meta['duration_min']} 分钟", flush=True)
    audio = os.path.join(d, "audio.m4a")
    download(meta["audio_url"], audio)
    cost, dur = transcribe(audio, os.path.join(d, "transcript.txt"))
    if dur < meta["duration_min"] * 60 * 0.95:
        print(f"警告：解码出的音频只有 {dur/60:.0f} 分钟，少于节目时长 {meta['duration_min']} 分钟，请检查音频文件")
    print(f"转写完成：音频 {dur/60:.0f} 分钟，用时 {cost/60:.1f} 分钟 → {d}/transcript.txt")


if __name__ == "__main__":
    main()
