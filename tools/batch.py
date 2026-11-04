"""靈幻之鑰: lk/chNN.popo.txt -> docs/audio/eNN.mp3; season = 卷 (10 chapters each).

Chapter titles and volume names come from 靈幻之鑰_逐章大綱.md. Skips existing audio;
regenerates when the chapter text is newer than its MP3. Updates episodes.json.
"""
import glob, json, os, re, subprocess, sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
BRAIN = os.path.expanduser("~/.gemini/jetski/brain/65a7a63d-68e1-4ec2-bbcc-730a51b2f9dd")
SRC = f"{BRAIN}/lk"
CN = "零一二三四五六七八九"
def cn(n): return CN[n] if n < 10 else ("十" + (CN[n % 10] if n % 10 else "") if n < 20 else CN[n // 10] + "十" + (CN[n % 10] if n % 10 else ""))
outline = open(f"{BRAIN}/靈幻之鑰_逐章大綱.md", encoding="utf-8").read()
TITLES = {int(n): t.strip() for n, t in re.findall(r"^(\d+)\. \*\*(.+?)\*\*", outline, re.M)}
KT = f"{SRC}/titles.json"  # final chapter titles as published on KadoKado (preferred over the outline)
KTITLES = json.load(open(KT, encoding="utf-8")) if os.path.exists(KT) else {}
VOLS = {i + 1: v.strip() for i, v in enumerate(re.findall(r"^## 第.卷　(.+?)（", outline, re.M))}
eps = json.load(open("episodes.json", encoding="utf-8")) if os.path.exists("episodes.json") else []
have = {e["file"] for e in eps}
MAX_NEW = int(os.environ.get("MAX_NEW", "12"))  # cap per run so the hourly cron pushes in small batches
made = 0
def save():  # atomic write: a crash mid-dump must not leave an empty episodes.json
    json.dump(sorted(eps, key=lambda e: (e["season"], e["n"])), open("episodes.json.tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace("episodes.json.tmp", "episodes.json")
base = datetime(2026, 11, 2, 12, tzinfo=timezone(timedelta(hours=8)))
for txt in sorted(glob.glob(f"{SRC}/ch[0-9][0-9].popo.txt")):
    if made >= MAX_NEW: break
    n = int(re.search(r"ch(\d+)\.popo", txt).group(1))
    if KTITLES and str(n) not in KTITLES:
        continue  # still being written: titles.json gets the title only once the volume is done
    season = (n - 1) // 10 + 1
    name = TITLES.get(n, "")
    title = KTITLES.get(str(n)) or (f"第{cn(n)}章　{name}" if name else f"第{cn(n)}章")
    f = f"e{n:02d}.mp3"
    mp3 = f"docs/audio/{f}"
    if os.path.exists(mp3) and os.path.getmtime(txt) > os.path.getmtime(mp3) + 60:
        os.remove(mp3)  # chapter text was edited after the audio was made: regenerate
    vol = VOLS.get(season, "")
    meta = {"title": f"靈幻之鑰｜{title}", "summary": f"《靈幻之鑰》第{cn(season)}卷「{vol}」　{title}。"}
    old = next((e for e in eps if e["file"] == f), None)
    if old and old["title"] != meta["title"]:
        old.update(meta)  # chapter renamed: the spoken intro has the old title, so regenerate
        if os.path.exists(mp3): os.remove(mp3)
    if f in have and os.path.exists(mp3):
        continue
    if not os.path.exists(mp3):
        subprocess.run([sys.executable, "-u", "tools/tts.py", txt, mp3,
                        f"靈幻之鑰。{title.replace('　', '，')}。", f"第{cn(n)}章，完。感謝收聽靈幻之鑰。"], check=True)
        made += 1
    if f not in have:
        eps.append({"n": n, "season": season, "file": f, **meta,
                    "pub": format_datetime(base + timedelta(minutes=n))})
        have.add(f)
    save()
    print("done", f, flush=True)
