#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, urllib.request

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "probe/3.0"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEAD)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

if not KEY:
    print("!!! KEY missing - check Secret name APIFOOTBALL_KEY")
    raise SystemExit(1)

print("=" * 55)
print("1) Search team 'Ittihad':")
saudi_id = None
try:
    d = get("/teams?search=ittihad")
    for item in d.get("response", []):
        t = item.get("team", {})
        print(f"  id={t.get('id')} | {t.get('name')} | country={t.get('country')}")
        c = (t.get("country") or "").lower()
        if c in ("saudi-arabia", "saudi arabia"):
            saudi_id = t.get("id")
    print(f"  >>> Ittihad Jeddah id: {saudi_id}")
    print("  errors:", d.get("errors"))
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("2) Ittihad fixtures season 2026 (all competitions):")
try:
    if saudi_id:
        d = get(f"/fixtures?team={saudi_id}&season=2026")
        resp = d.get("response", [])
        print(f"  total fixtures: {len(resp)}")
        print("  errors:", d.get("errors"))
        if resp:
            print("  --- FIRST FIXTURE ---")
            print(json.dumps(resp[0], ensure_ascii=False, indent=2)[:1500])
            print("  --- competitions ---")
            comps = sorted(set(f.get("league", {}).get("name", "?") for f in resp))
            for c in comps:
                print("   -", c)
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("probe v3 done.")
