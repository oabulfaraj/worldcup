#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ittihad.py - Al-Ittihad Jeddah calendar, auto-updated.
API-Football: fixtures, results, Ittihad goals/cards/subs, possession, standings.
Cache: finished matches (>1 day) read from saved file, not re-fetched.
"""
import json, os, urllib.request, time
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "ittihad-cal/3.2"}
TEAM = 2938
SEASON = "2026"
SEASON_START = "2026-07-01"
PRO_LEAGUE_ID = 307
OUT = "worldcup2026.ics"
CACHE = "events_cache_v3.json"
ITTIHAD_NAMES = {"al-ittihad fc","al ittihad","al-ittihad"}

SAUDI_CLUBS = {
    "al-ittihad fc","al ittihad","al-hilal saudi fc","al-hilal","al hilal",
    "al-nassr","al nassr","al-ahli jeddah","al-ahli saudi","al ahli",
    "al-shabab","al shabab","al-ettifaq","al-ettifaq fc","al-fateh","al fateh",
    "al-fayha","al fayha","al-taawoun","al taawon","al-hazem","al hazm",
    "al-khaleej","al khaleej","al-kholood","al kholood","al-qadisiyah fc",
    "al-qadisiyah","al quadisiya","al-riyadh","al riyadh","al-faisaly",
    "al faisaly","al-okhdood","abha","neom","neom sc","al-najma","al najma",
    "al-jandal","al-orobah","al-orubah",
}
FOREIGN_FLAG = {
    "al-ain":"🇦🇪","al ain":"🇦🇪","shabab al-ahli":"🇦🇪","shabab al ahli dubai":"🇦🇪",
    "al-wasl":"🇦🇪","al wasl":"🇦🇪","al-jazira":"🇦🇪","al jazira":"🇦🇪",
    "al-sadd":"🇶🇦","al sadd":"🇶🇦","al-gharafa":"🇶🇦","al gharafa":"🇶🇦",
    "al-shamal":"🇶🇦","al shamal":"🇶🇦","al-duhail":"🇶🇦","al-rayyan":"🇶🇦",
    "pakhtakor":"🇺🇿","neftchi fergana":"🇺🇿","neftchi":"🇺🇿","nasaf":"🇺🇿","agmk":"🇺🇿",
    "esteghlal":"🇮🇷","persepolis":"🇮🇷","sepahan":"🇮🇷","tractor":"🇮🇷",
    "al-shorta":"🇮🇶","al shorta":"🇮🇶","air force club":"🇮🇶",
    "al-quwa al-jawiya":"🇮🇶","al-kuwait":"🇰🇼","al kuwait":"🇰🇼","sharjah":"🇦🇪",
}
COMP_AR = {
    "Pro League":"دوري روشن","King's Cup":"كأس الملك","Super Cup":"كأس السوبر",
    "AFC Champions League Elite":"دوري أبطال آسيا للنخبة",
    "AFC Champions League":"دوري أبطال آسيا","Friendlies Clubs":"ودية",
}

def team_flag(name):
    n=(name or "").strip().lower()
    if n in ITTIHAD_NAMES: return "🟡⚫"
    if "ahli" in n and ("jeddah" in n or "saudi" in n or n=="al ahli"): return "🐸"
    if n in SAUDI_CLUBS: return ""
    if n in FOREIGN_FLAG: return FOREIGN_FLAG[n]
    return ""

def is_ittihad(name):
    return (name or "").strip().lower() in ITTIHAD_NAMES

def fetch(path, tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(BASE+path,headers=HEAD)
            with urllib.request.urlopen(req,timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"try {i+1} failed: {e}")
            if i<tries-1: time.sleep(3)
    return None

def parse_dt(iso):
    try: return datetime.fromisoformat((iso or "").replace("Z","+00:00")).astimezone(timezone.utc)
    except: return None

def fold(line):
    raw=line.encode("utf-8");out=[]
    while len(raw)>73:
        out.append(raw[:73].decode("utf-8","ignore"));raw=b" "+raw[73:]
    out.append(raw.decode("utf-8","ignore"))
    return "\r\n".join(out)

FINISHED={"FT","AET","PEN"}

def load_cache():
    try:
        with open(CACHE,encoding="utf-8") as f: return json.load(f)
    except: return {}

def save_cache(c):
    try:
        with open(CACHE,"w",encoding="utf-8") as f: json.dump(c,f,ensure_ascii=False)
    except Exception as e: print("cache save error:",e)

def get_standings():
    out={}
    d=fetch(f"/standings?league={PRO_LEAGUE_ID}&season={SEASON}")
    try:
        for row in d["response"][0]["league"]["standings"][0]:
            nm=(row.get("team",{}).get("name","") or "").strip().lower()
            out[nm]=(row.get("rank"),row.get("points"))
    except Exception as e: print("standings error:",e)
    return out

def fetch_possession(fid):
    """Ball possession % per team name."""
    d=fetch(f"/fixtures/statistics?fixture={fid}")
    poss={}
    for blk in (d or {}).get("response",[]):
        tm=blk.get("team",{}).get("name") or ""
        for st in blk.get("statistics",[]):
            if st.get("type")=="Ball Possession" and st.get("value"):
                poss[tm]=str(st.get("value"))
    return poss

def fetch_events(fid):
    """Ittihad goals/cards/subs only, plus possession."""
    d=fetch(f"/fixtures/events?fixture={fid}")
    goals=[]; itt_cards=[]; subs=[]
    for e in (d or {}).get("response",[]):
        typ=e.get("type"); dtl=e.get("detail","")
        mn=e.get("time",{}).get("elapsed")
        pl=e.get("player",{}).get("name") or ""
        tm=e.get("team",{}).get("name") or ""
        itt=is_ittihad(tm)
        if typ=="Goal" and "Missed" not in dtl:
            own="Own" in dtl
            if (itt and not own) or (not itt and own):
                goals.append([mn,pl])
        elif typ=="Card" and itt:
            ic = "🟥" if "Red" in dtl else "🟨"
            itt_cards.append([mn,pl,ic])
        elif typ=="subst" and itt:
            inp=pl; outp=e.get("assist",{}).get("name") or ""
            subs.append([mn,inp,outp])
    poss=fetch_possession(fid)
    return {"goals":goals,"cards":itt_cards,"subs":subs,"poss":poss}

def get_events(fid, start_utc, cache):
    key=str(fid)
    day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    if key in cache and start_utc < day_ago:
        return cache[key]
    ev=fetch_events(fid)
    cache[key]=ev
    return ev

def main():
    if not KEY: raise SystemExit("!!! APIFOOTBALL_KEY missing")
    data=fetch(f"/fixtures?team={TEAM}&season={SEASON}")
    if not data or not data.get("response"): raise SystemExit("!!! no fixtures")
    fixtures=data["response"]
    print(f"fetched {len(fixtures)} fixtures")

    standings=get_standings()
    cache=load_cache()

    now=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//Ittihad//Omar Calendar//EN",
       "CALSCALE:GREGORIAN","METHOD:PUBLISH",
       "X-WR-CALNAME:Omar's Ittihad / مباريات الاتحاد 🟡⚫","X-WR-TIMEZONE:UTC",
       "X-WR-CALDESC:Al-Ittihad Jeddah - all competitions, auto-updated",
       "REFRESH-INTERVAL;VALUE=DURATION:PT1H","X-PUBLISHED-TTL:PT1H"]

    today=datetime.now(timezone.utc).strftime("%Y%m%d")
    L+=["BEGIN:VEVENT","UID:ittihad-welcome-2026@omar-calendar",f"DTSTAMP:{now}",
        f"DTSTART;VALUE=DATE:{today}",
        fold("SUMMARY:👋 Welcome to Al-Ittihad Calendar 🟡⚫"),
        fold("DESCRIPTION:Enjoy following George Ilenikhena and his teammates — all competitions and results 🟡⚫"),
        "TRANSP:TRANSPARENT","END:VEVENT"]

    count=0
    for f in fixtures:
        fx=f.get("fixture",{}); lg=f.get("league",{}); teams=f.get("teams",{}); goals=f.get("goals",{})
        start=parse_dt(fx.get("date",""))
        if not start: continue
        if start.strftime("%Y-%m-%d")<SEASON_START: continue
        end=start+timedelta(minutes=120)
        uid=f"ittihad-{fx.get('id','x')}@omar-calendar"

        home=teams.get("home",{}).get("name","?"); away=teams.get("away",{}).get("name","?")
        hf=team_flag(home); af=team_flag(away)
        h_disp=(hf+" "+home).strip(); a_disp=(af+" "+away).strip()

        status=fx.get("status",{}).get("short",""); gh,ga=goals.get("home"),goals.get("away")
        played=status in FINISHED and gh is not None and ga is not None
        summary=f"{h_disp} {gh} - {ga} {a_disp}" if played else f"{h_disp} vs {a_disp}"

        comp=lg.get("name",""); comp_disp=f"{COMP_AR.get(comp,comp)} / {comp}" if comp in COMP_AR else comp
        desc=[f"🏆 {comp_disp}"]

        ev=None
        if played:
            ev=get_events(fx.get("id"),start,cache)
            gmap={}
            for m,p in ev.get("goals",[]):
                if m is None: continue
                gmap.setdefault(p,[]).append(m)
            if gmap:
                desc.append("")
                desc.append("⚽ Goals:")
                for p,mins in gmap.items():
                    mins=sorted(mins)
                    desc.append(f"   {p} "+", ".join(f"{x}'" for x in mins))
            cards=[(m,p,ic) for m,p,ic in ev.get("cards",[]) if m is not None]
            if cards:
                desc.append("")
                desc.append("Cards (Ittihad):")
                for m,p,ic in cards:
                    desc.append(f"   {ic} {p} {m}'")
            subs=[(m,inp,outp) for m,inp,outp in ev.get("subs",[]) if m is not None]
            if subs:
                desc.append("")
                desc.append("🔄 Subs (Ittihad):")
                for m,inp,outp in subs:
                    desc.append(f"   {inp} ⬆️ {outp} ⬇️ {m}'")

        tail=[]
        if played and ev:
            poss=ev.get("poss",{}) or {}
            ph=poss.get(home); pa=poss.get(away)
            if ph and pa:
                tail.append(f"⚖️ Possession — {home}: {ph} · {away}: {pa}")

        if comp=="Pro League":
            fid=str(fx.get("id"))
            stand_key=f"stand_{fid}"
            if played:
                if stand_key in cache:
                    frozen=cache[stand_key]
                else:
                    frozen={"h":standings.get(home.strip().lower()),
                            "a":standings.get(away.strip().lower())}
                    cache[stand_key]=frozen
                hs=frozen.get("h"); as_=frozen.get("a")
            else:
                hs=standings.get(home.strip().lower()); as_=standings.get(away.strip().lower())
            if hs and as_:
                tail.append(f"📊 {home}: #{hs[0]} ({hs[1]} pts) · {away}: #{as_[0]} ({as_[1]} pts)")

        if tail:
            desc.append("")
            desc.extend(tail)

        d="\\n".join(desc)
        venue=fx.get("venue",{}).get("name",""); city=fx.get("venue",{}).get("city","")
        loc=", ".join(x for x in [venue,city] if x)

        L+=["BEGIN:VEVENT",f"UID:{uid}",f"DTSTAMP:{now}",
            f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
            fold(f"SUMMARY:{summary}"),fold(f"DESCRIPTION:{d}")]
        if loc: L.append(fold(f"LOCATION:{loc}"))
        L+=["STATUS:CONFIRMED","TRANSP:TRANSPARENT","END:VEVENT"]
        count+=1

    L.append("END:VCALENDAR")
    with open(OUT,"w",encoding="utf-8") as fp: fp.write("\r\n".join(L)+"\r\n")
    save_cache(cache)
    print(f"OK: wrote {count} matches to {OUT}")

if __name__=="__main__":
    main()
