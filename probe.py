#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, urllib.request

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "probe/6.0"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEAD)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

TEAM = 2938

for season in ("2026", "2025"):
    print("=" * 55)
    print(f"season={season}:")
    try:
        d = get(f"/fixtures?team={TEAM}&season={season}")
        resp = d.get("response", [])
        dates = sorted(f.get("fixture", {}).get("date", "")[:10] for f in resp if f.get("fixture", {}).get("date"))
        print(f"  total: {len(resp)}")
        if dates:
            print(f"  earliest match: {dates[0]}")
            print(f"  latest match:   {dates[-1]}")
        current = [x for x in dates if x >= "2026-07-01"]
        print(f"  matches from 2026-07-01 onward: {len(current)}")
        if current:
            print(f"    first current-season date: {current[0]}")
    except Exception as e:
        print("  error:", e)

print("=" * 55)
print("probe v6 done.")
