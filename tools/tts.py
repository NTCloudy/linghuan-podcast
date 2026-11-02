"""Chapter text -> MP3 with edge-tts (zh-TW male), chunked + concatenated."""
import asyncio, re, subprocess, sys, tempfile, os
import edge_tts
VOICE = os.environ.get("VOICE", "zh-CN-YunxiNeural")

def clean(text):
    text = re.sub(r"^【[一二三四五六七八九十]+】\s*$", "……", text, flags=re.M)
    text = text.replace("——", "，").replace("……", "。")
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def chunks(text, n=1200):
    out, cur = [], ""
    for para in text.split("\n"):
        if len(cur) + len(para) > n and cur:
            out.append(cur); cur = ""
        cur += para + "\n"
    if cur.strip(): out.append(cur)
    return out

async def synth(text, path):
    for attempt in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate="+0%").save(path); return
        except Exception as e:
            print("retry", e, flush=True); await asyncio.sleep(3 * (attempt + 1))
    raise RuntimeError("tts failed")

def main(src, out, intro, outro):
    body = clean(open(src, encoding="utf-8").read())
    parts = [intro] + chunks(body) + [outro]
    with tempfile.TemporaryDirectory() as td:
        files = []
        for i, t in enumerate(parts):
            p = f"{td}/{i:03d}.mp3"; asyncio.run(synth(t, p)); files.append(p)
        lst = f"{td}/list.txt"
        open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-ac", "1", "-ar", "24000", "-b:a", "64k", out], check=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                         capture_output=True, text=True).stdout.strip()
    print(out, dur)

if __name__ == "__main__":
    main(*sys.argv[1:5])
