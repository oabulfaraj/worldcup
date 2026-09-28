#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, urllib.request

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "probe/8.0"}

def get(path):
    req = urllib.request.Request(BASE + path, headers=HEAD)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

TEAM = 2938
d = get(f"/fixtures?team={TEAM}&season=2026")
resp = d.get("response", [])

print("=" * 55)
print("1) Pro League id + team countries:")
league_id = None
for f in resp:
    lg = f.get("league", {})
    if lg.get("name") == "Pro League":
        league_id = lg.get("id")
        print(f"  Pro League id: {league_id}, season: {lg.get('season')}")
        break
for name in ["Al-Ahli","Al-Ain","Al-Sadd"]:
    try:
        dd = get(f"/teams?search={name}")
        for it in dd.get("response",[])[:1]:
            tt=it.get("team",{})
            print(f"    {tt.get('name')} | id={tt.get('id')} | country={tt.get('country')}")
    except Exception as e:
        print("    err",e)

print("=" * 55)
print("2) Events for a finished match:")
try:
    played = [f for f in resp if f.get("fixture",{}).get("status",{}).get("short") in ("FT","AET","PEN")]
    if played:
        fm = played[-1]
        fid = fm.get("fixture",{}).get("id")
        print(f"  {fm.get('teams',{}).get('home',{}).get('name')} vs {fm.get('teams',{}).get('away',{}).get('name')} (id={fid})")
        ev = get(f"/fixtures/events?fixture={fid}").get("response", [])
        for typ in ("Goal","Card","subst"):
            items=[e for e in ev if e.get("type")==typ]
            print(f"  --- {typ} ({len(items)}) ---")
            for e in items[:4]:
                print(f"    {e.get('time',{}).get('elapsed')}' | {e.get('team',{}).get('name')} | player={e.get('player',{}).get('name')} | assist={e.get('assist',{}).get('name')} | detail={e.get('detail')}")
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("3) Standings:")
try:
    if league_id:
        st = get(f"/standings?league={league_id}&season=2026")
        tables = st.get("response",[{}])[0].get("league",{}).get("standings",[[]])
        for row in tables[0][:6]:
            print(f"    #{row.get('rank')} {row.get('team',{}).get('name')} - {row.get('points')} pts (P{row.get('all',{}).get('played')})")
except Exception as e:
    print("  error:", e)

print("=" * 55)
print("probe v8 done.")
