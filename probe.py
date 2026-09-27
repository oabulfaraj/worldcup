#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, urllib.request

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "probe/5.0"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEAD)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

TEAM = 2938

for season in ("2026", "2025"):
    print("=" * 55)
    print(f"Season {season}:")
    try:
        d = get(f"/fixtures?team={TEAM}&season={season}")
        resp = d.get("response", [])
        print(f"  total fixtures: {len(resp)}")
        print("  errors:", d.get("errors"))
        if resp:
            comps = sorted(set(f.get("league", {}).get("name", "?") for f in resp))
            print("  competitions:", ", ".join(comps))
            for f in resp[:3]:
                lg = f.get("league", {}).get("name", "?")
                h = f.get("teams", {}).get("home", {}).get("name", "?")
                a = f.get("teams", {}).get("away", {}).get("name", "?")
                dt = f.get("fixture", {}).get("date", "?")
                st = f.get("fixture", {}).get("status", {}).get("short", "?")
                gh = f.get("goals", {}).get("home")
                ga = f.get("goals", {}).get("away")
                print(f"    {dt[:16]} | {h} {gh}-{ga} {a} | {lg} | {st}")
    except Exception as e:
        print("  error:", e)

print("=" * 55)
print("probe v5 done.")
