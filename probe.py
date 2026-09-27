#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, urllib.request

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "probe/4.0"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEAD)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

TEAM = 2938  # Al-Ittihad FC (men, Jeddah)

print("=" * 55)
print(f"Ittihad (id={TEAM}) fixtures season 2024 (all competitions):")
try:
    d = get(f"/fixtures?team={TEAM}&season=2024")
    resp = d.get("response", [])
    print(f"  total fixtures: {len(resp)}")
    print("  errors:", d.get("errors"))
    if resp:
        comps = sorted(set(f.get("league", {}).get("name", "?") for f in resp))
        print("  --- competitions ---")
        for c in comps:
            print("   -", c)
        print("  --- FIRST FIXTURE ---")
        print(json.dumps(resp[0], ensure_ascii=False, indent=2)[:1800])
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("probe v4 done.")
