#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ittihad.py — تقويم مباريات نادي الاتحاد (جدة) — تحديث تلقائي
يسحب مباريات الاتحاد من API-Football (كل البطولات) ويولّد ittihad.ics
بأعلام الأندية، النتائج، الملعب، والبطولة، بتوقيت UTC.
يقرأ المفتاح من متغيّر البيئة APIFOOTBALL_KEY (GitHub Secret).
"""
import json, os, urllib.request, time
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("APIFOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
HEAD = {"x-apisports-key": KEY, "User-Agent": "ittihad-cal/1.0"}
TEAM = 2938          # Al-Ittihad FC (men, Jeddah)
SEASON = "2026"      # موسم API-Football الذي يغطّي 2026/2027
SEASON_START = "2026-07-01"  # نعرض فقط مباريات الموسم الحالي (يوليو 2026 فصاعداً)
OUT = "ittihad.ics"

# ---------- ترجمة البطولات ----------
COMP_AR = {
    "Pro League": "دوري روشن",
    "King's Cup": "كأس الملك",
    "Super Cup": "كأس السوبر",
    "AFC Champions League Elite": "دوري أبطال آسيا للنخبة",
    "AFC Champions League": "دوري أبطال آسيا",
    "Friendlies Clubs": "ودية",
}

# ---------- أعلام حسب دولة النادي المنافس ----------
# الاتحاد نفسه بألوانه؛ البقية حسب الدولة (من حقل country في الـ league أو تخمين)
FLAG = {
    "Al-Ittihad FC": "🟡⚫", "Al Ittihad": "🟡⚫",
}
# أعلام حسب دولة (نستخدمها لو ما عرفنا النادي)
COUNTRY_FLAG = {
    "Saudi Arabia": "🇸🇦", "Saudi-Arabia": "🇸🇦",
    "United Arab Emirates": "🇦🇪", "United-Arab-Emirates": "🇦🇪",
    "Qatar": "🇶🇦", "Uzbekistan": "🇺🇿", "Iran": "🇮🇷", "Iraq": "🇮🇶",
    "Egypt": "🇪🇬", "Morocco": "🇲🇦", "Spain": "🇪🇸", "Japan": "🇯🇵",
}

def team_flag(name, country=None):
    if name in FLAG:
        return FLAG[name]
    if country and country in COUNTRY_FLAG:
        return COUNTRY_FLAG[country]
    # افتراضياً السعودية (أغلب الخصوم محليون)
    return "🇸🇦"

# ---------- جلب البيانات مع حماية ----------
def fetch(path, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(BASE + path, headers=HEAD)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print(f"محاولة {i+1} فشلت: {e}")
            if i < tries - 1:
                time.sleep(3)
    return None

def parse_dt(iso):
    """يحوّل '2026-10-10T18:00:00+00:00' إلى datetime UTC."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def fold(line):
    raw = line.encode("utf-8"); out = []
    while len(raw) > 73:
        out.append(raw[:73].decode("utf-8", "ignore")); raw = b" " + raw[73:]
    out.append(raw.decode("utf-8", "ignore"))
    return "\r\n".join(out)

# الحالات المنتهية (فيها نتيجة نهائية)
FINISHED = {"FT", "AET", "PEN"}

def main():
    if not KEY:
        raise SystemExit("!!! المفتاح غير موجود (APIFOOTBALL_KEY)")

    data = fetch(f"/fixtures?team={TEAM}&season={SEASON}")
    if not data or not data.get("response"):
        raise SystemExit("!!! لم تُسحب أي مباريات — تحقق من الاشتراك/المفتاح")
    fixtures = data["response"]
    print(f"سُحبت {len(fixtures)} مباراة")

    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR", "VERSION:2.0",
         "PRODID:-//Ittihad//Omar Calendar//EN",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
         "X-WR-CALNAME:Omar's Ittihad / مباريات الاتحاد 🟡⚫",
         "X-WR-TIMEZONE:UTC",
         "X-WR-CALDESC:Al-Ittihad Jeddah - all competitions, auto-updated",
         "REFRESH-INTERVAL;VALUE=DURATION:PT1H", "X-PUBLISHED-TTL:PT1H"]

    count = 0
    for f in fixtures:
        fx = f.get("fixture", {})
        lg = f.get("league", {})
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        score = f.get("score", {})

        start = parse_dt(fx.get("date", ""))
        if not start:
            continue
        # فلتر: فقط مباريات الموسم الحالي (يوليو 2026 فصاعداً)
        if start.strftime("%Y-%m-%d") < SEASON_START:
            continue
        end = start + timedelta(minutes=120)
        uid = f"ittihad-{fx.get('id','x')}@omar-calendar"

        home = teams.get("home", {}).get("name", "?")
        away = teams.get("away", {}).get("name", "?")
        h_flag = team_flag(home)
        a_flag = team_flag(away)
        h_disp = f"{h_flag} {home}"
        a_disp = f"{a_flag} {away}"

        status = fx.get("status", {}).get("short", "")
        gh = goals.get("home")
        ga = goals.get("away")
        played = status in FINISHED and gh is not None and ga is not None

        if played:
            summary = f"{h_disp} {gh} - {ga} {a_disp}"
        else:
            summary = f"{h_disp} vs {a_disp}"

        # الوصف: البطولة (عربي/إنجليزي) + ركلات ترجيح لو وُجدت
        comp = lg.get("name", "")
        comp_disp = f"{COMP_AR.get(comp, comp)} / {comp}" if comp in COMP_AR else comp
        desc_lines = [f"🏆 {comp_disp}"]
        if status == "PEN":
            pen = score.get("penalty", {})
            ph, pa = pen.get("home"), pen.get("away")
            if ph is not None and pa is not None:
                desc_lines.append(f"ركلات الترجيح / Penalties: {ph} - {pa}")
        desc = "\\n".join(desc_lines)

        venue = fx.get("venue", {}).get("name", "")
        city = fx.get("venue", {}).get("city", "")
        loc = ", ".join(x for x in [venue, city] if x)

        L += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{now}",
              f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
              f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
              fold(f"SUMMARY:{summary}"), fold(f"DESCRIPTION:{desc}")]
        if loc:
            L.append(fold(f"LOCATION:{loc}"))
        L += ["STATUS:CONFIRMED", "TRANSP:TRANSPARENT", "END:VEVENT"]
        count += 1

    L.append("END:VCALENDAR")
    with open(OUT, "w", encoding="utf-8") as fp:
        fp.write("\r\n".join(L) + "\r\n")
    print(f"OK: كُتبت {count} مباراة إلى {OUT}")

if __name__ == "__main__":
    main()
