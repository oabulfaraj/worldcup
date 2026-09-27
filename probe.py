#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe.py (v2) — فحص أدق لإيجاد اتحاد جدة الصحيح في TheSportsDB.
"""
import json, urllib.request

API_KEY = "123"
BASE = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "probe/2.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

print("=" * 55)
print("1) All teams named Ittihad:")
try:
    d = get(f"{BASE}/searchteams.php?t=Ittihad")
    for t in (d.get("teams") or []):
        print(f"  id={t.get('idTeam')} | {t.get('strTeam')} | "
              f"{t.get('strLeague')} | {t.get('strCountry')}")
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("2) All Saudi Pro League teams (league 4668):")
saudi_ittihad_id = None
try:
    d = get(f"{BASE}/lookup_all_teams.php?id=4668")
    for t in (d.get("teams") or []):
        name = t.get('strTeam','')
        if 'ittihad' in name.lower():
            print(f"  *** id={t.get('idTeam')} | {name} | {t.get('strStadium')} ***")
            saudi_ittihad_id = t.get('idTeam')
        else:
            print(f"      id={t.get('idTeam')} | {name}")
    print(f"  >>> Ittihad Jeddah id: {saudi_ittihad_id}")
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("3) Next events (full sample):")
try:
    if saudi_ittihad_id:
        d = get(f"{BASE}/eventsnext.php?id={saudi_ittihad_id}")
        evs = d.get("events") or []
        print(f"  next count: {len(evs)}")
        if evs:
            print(json.dumps(evs[0], ensure_ascii=False, indent=2))
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("4) Last events (full sample):")
try:
    if saudi_ittihad_id:
        d = get(f"{BASE}/eventslast.php?id={saudi_ittihad_id}")
        evs = d.get("results") or d.get("events") or []
        print(f"  last count: {len(evs)}")
        if evs:
            print(json.dumps(evs[0], ensure_ascii=False, indent=2))
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("probe v2 done.")
