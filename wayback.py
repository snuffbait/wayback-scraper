import requests
import os
from datetime import datetime

os.makedirs("results", exist_ok=True)

agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.155 Safari/537.36"
out = []

def p(x=""):
    print(x)
    out.append(x)

def dump(q):
    t = datetime.now().strftime("%Y%m%d%H%M%S")
    n = "".join(c for c in q if c.isalnum())[:30]
    open(f"results/{n}{t}.txt", "w").write("\n".join(out))
    print(f"\n  saved to results/{n}{t}.txt")
    out.clear()

def ts(x):
    try:
        return datetime.strptime(x, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except:
        return x

def fix(url):
    if not url.startswith("http"):
        url = "https://" + url
    return url.rstrip("/")

def fetch(url, lim=None):
    q = {"url": url, "output": "json", "fl": "timestamp,statuscode,length,original", "collapse": "timestamp:8"}
    if lim:
        q["limit"] = lim
    try:
        r = requests.get("http://web.archive.org/cdx/search/cdx", params=q, headers={"User-Agent": agent}, timeout=20)
        d = r.json()
        if not d or len(d) < 2:
            return []
        h = d[0]
        return [dict(zip(h, row)) for row in d[1:]]
    except:
        return []

def hist(url):
    p(f"\n  all snapshots: {url}")
    data = fetch(url)
    if not data:
        p("  nothing")
        return
    p(f"  {len(data)} total\n")
    yrs = {}
    for s in data:
        y = s["timestamp"][:4]
        yrs.setdefault(y, []).append(s)
    codes = {"200": "ok", "301": "redirect", "302": "redirect", "404": "gone", "403": "blocked", "500": "error"}
    for y in sorted(yrs):
        p(f"  {y} ({len(yrs[y])})")
        for s in yrs[y]:
            p(f"    {ts(s['timestamp'])}  {s['statuscode']} ({codes.get(s['statuscode'], '?')})  {s.get('length','?')}b")
            p(f"    https://web.archive.org/web/{s['timestamp']}/{url}")
        p()

def new(url, n=10):
    p(f"\n  last {n}: {url}")
    q = {"url": url, "output": "json", "fl": "timestamp,statuscode,length", "limit": f"-{n}"}
    try:
        r = requests.get("http://web.archive.org/cdx/search/cdx", params=q, headers={"User-Agent": agent}, timeout=15)
        d = r.json()
        if not d or len(d) < 2:
            p("  nothing")
            return
        h = d[0]
        rows = [dict(zip(h, row)) for row in d[1:]]
        for s in reversed(rows):
            p(f"  {ts(s['timestamp'])}  {s['statuscode']}  {s.get('length','?')}b")
            p(f"  https://web.archive.org/web/{s['timestamp']}/{url}")
            p()
    except:
        p("  failed")

def diff(url):
    p(f"\n  changes: {url}")
    data = fetch(url)
    if not data:
        p("  nothing")
        return
    codes = {"200": "live", "301": "redirect", "302": "redirect", "404": "deleted", "403": "blocked", "500": "error"}
    prev = None
    for s in data:
        c = s.get("statuscode", "?")
        if c != prev:
            p(f"  {ts(s['timestamp'])}  {c} ({codes.get(c, c)})")
            p(f"  https://web.archive.org/web/{s['timestamp']}/{url}")
            p()
            prev = c

def main():
    while True:
        print("\n  wayback")
        print("  1 full history")
        print("  2 recent")
        print("  3 changes")

        c = input("\n  pick: ").strip().lower()
        if c not in "123":
            continue

        url = input("\n  url: ").strip()
        if not url:
            continue
        url = fix(url)

        if c == "1":
            hist(url)
            dump(url)
        elif c == "2":
            n = input("  how many (default 10): ").strip()
            new(url, int(n) if n.isdigit() else 10)
            dump(url)
        elif c == "3":
            diff(url)
            dump(url)

if __name__ == "__main__":
    main()
