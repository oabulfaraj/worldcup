#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
probe.py — سكربت فحص لمرة واحدة (يشتغل على GitHub Actions).
يسحب بيانات الاتحاد الحقيقية من TheSportsDB ويطبعها في السجل
عشان نتأكد من البنية قبل بناء التقويم الكامل.
"""
import json, urllib.request

API_KEY = "123"
BASE = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "probe/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

print("=" * 55)
print("١) البحث عن الاتحاد (searchteams):")
team_id = None
try:
    d = get(f"{BASE}/searchteams.php?t=Al-Ittihad")
    for t in (d.get("teams") or []):
        print(f"  id={t.get('idTeam')} | {t.get('strTeam')} | "
              f"league={t.get('strLeague')} | country={t.get('strCountry')}")
        lg = (t.get('strLeague') or '').lower()
        co = (t.get('strCountry') or '').lower()
        if 'saudi' in lg or 'saudi' in co:
            team_id = t.get('idTeam')
    print(f"  >>> معرّف اتحاد جدة المُختار: {team_id}")
except Exception as e:
    print("  خطأ:", e)

print("=" * 55)
print("٢) مباريات الاتحاد القادمة (eventsnext) — عيّنة أول حدث كامل:")
try:
    if team_id:
        d = get(f"{BASE}/eventsnext.php?id={team_id}")
        evs = d.get("events") or []
        print(f"  عدد المباريات القادمة: {len(evs)}")
        if evs:
            print(json.dumps(evs[0], ensure_ascii=False, indent=2))
except Exception as e:
    print("  خطأ:", e)

print("=" * 55)
print("٣) مباريات الاتحاد الماضية (eventslast) — عيّنة أول حدث كامل:")
try:
    if team_id:
        d = get(f"{BASE}/eventslast.php?id={team_id}")
        evs = d.get("results") or d.get("events") or []
        print(f"  عدد المباريات الماضية: {len(evs)}")
        if evs:
            print(json.dumps(evs[0], ensure_ascii=False, indent=2))
except Exception as e:
    print("  خطأ:", e)

print("=" * 55)
print("٤) موسم دوري روشن (eventsseason) — عدد أحداث الاتحاد فيه:")
try:
    d = get(f"{BASE}/eventsseason.php?id=4668&s=2026-2027")
    evs = d.get("events") or []
    itt = [e for e in evs if 'ittihad' in (e.get('strHomeTeam','')+e.get('strAwayTeam','')).lower()]
    print(f"  إجمالي أحداث الموسم: {len(evs)} | منها للاتحاد: {len(itt)}")
    if itt:
        e = itt[0]
        print(f"  مثال: {e.get('dateEvent')} {e.get('strHomeTeam')} vs {e.get('strAwayTeam')} | {e.get('strLeague')}")
except Exception as e:
    print("  خطأ:", e)

print("=" * 55)
print("تم الفحص بنجاح.")
