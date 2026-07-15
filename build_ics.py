
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ics.py  —  تقويم كأس العالم ٢٠٢٦ (تحديث تلقائي)
يسحب الجدول والنتائج الحيّة من مصدر openfootball المجاني (بدون مفتاح API)
ويولّد worldcup2026.ics بأسماء عربية/إنجليزية وبتوقيت UTC.
 
يشتغل تلقائياً عبر GitHub Actions يومياً. ما يحتاج أي تدخل يدوي.
"""
 
import json, re, urllib.request, csv, io
from collections import defaultdict
from datetime import datetime, timedelta, timezone
 
SOURCE = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"
H2H_SOURCE = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
OUT = "worldcup2026.ics"
 
# ---------- تحميل السجل التاريخي للمواجهات بين المنتخبات ----------
def load_h2h():
    """يحمّل المباريات الدولية للسجل التاريخي.
    متسامح مع الأخطاء: لو فشل التحميل، النظام يكمل بدون سجل (لا يتعطّل التقويم)."""
    h2h = defaultdict(list)
    try:
        req = urllib.request.Request(H2H_SOURCE, headers={"User-Agent": "worldcup-cal"})
        with urllib.request.urlopen(req, timeout=20) as r:
            text = r.read().decode("utf-8")
        for row in csv.DictReader(io.StringIO(text)):
            if row["home_score"] in ("NA","") or row["away_score"] in ("NA",""):
                continue
            key = frozenset([row["home_team"], row["away_team"]])
            h2h[key].append(row)
        print(f"تم تحميل السجل التاريخي: {len(h2h)} زوج فرق")
    except Exception as e:
        print("تحذير: تعذّر تحميل السجل التاريخي، سيتم إنشاء التقويم بدونه:", e)
    return h2h
 
def h2h_text(a, b, h2h):
    """يبني سطر السجل التاريخي بين منتخبين (إنجليزي)."""
    # مطابقة الأسماء المختلفة بين المصدرين
    NAME_MAP = {
        "Czechia": "Czech Republic", "USA": "United States",
        "Turkiye": "Turkey", "Curacao": "Curaçao",
    }
    a = NAME_MAP.get(a, a)
    b = NAME_MAP.get(b, b)
    matches = h2h.get(frozenset([a, b]), [])
    if not matches:
        return "First-ever meeting between the two teams"
    wa = wb = draws = 0
    for m in matches:
        try:
            hs, as_ = int(m["home_score"]), int(m["away_score"])
        except ValueError:
            continue
        if hs == as_:
            draws += 1
        else:
            winner = m["home_team"] if hs > as_ else m["away_team"]
            if winner == a: wa += 1
            else: wb += 1
    last = matches[-1]
    line1 = f"📊 Head-to-head: {len(matches)} meetings — {a} {wa}W, {b} {wb}W, {draws}D"
    line2 = f"Last: {last['date']} {last['home_team']} {last['home_score']}-{last['away_score']} {last['away_team']}"
    return line1 + "\\n" + line2
 
# ---------- أسماء المنتخبات بالعربي ----------
AR = {
    "Mexico":"المكسيك","South Africa":"جنوب أفريقيا","South Korea":"كوريا الجنوبية",
    "Czech Republic":"التشيك","Czechia":"التشيك","Canada":"كندا",
    "Bosnia and Herzegovina":"البوسنة والهرسك","Bosnia-Herzegovina":"البوسنة والهرسك",
    "United States":"أمريكا","USA":"أمريكا","Paraguay":"باراغواي","Qatar":"قطر",
    "Switzerland":"سويسرا","Brazil":"البرازيل","Morocco":"المغرب","Haiti":"هايتي",
    "Scotland":"اسكتلندا","Australia":"أستراليا","Turkey":"تركيا","Türkiye":"تركيا",
    "Turkiye":"تركيا","Germany":"ألمانيا","Curacao":"كوراساو","Curaçao":"كوراساو",
    "Netherlands":"هولندا","Japan":"اليابان","Ivory Coast":"ساحل العاج",
    "Côte d'Ivoire":"ساحل العاج","Ecuador":"الإكوادور","Sweden":"السويد","Tunisia":"تونس",
    "Spain":"إسبانيا","Cape Verde":"الرأس الأخضر","Cabo Verde":"الرأس الأخضر",
    "Belgium":"بلجيكا","Egypt":"مصر","Saudi Arabia":"السعودية","Uruguay":"الأوروجواي",
    "Iran":"إيران","IR Iran":"إيران","New Zealand":"نيوزيلندا","France":"فرنسا",
    "Senegal":"السنغال","Iraq":"العراق","Norway":"النرويج","Argentina":"الأرجنتين",
    "Algeria":"الجزائر","Austria":"النمسا","Jordan":"الأردن","Portugal":"البرتغال",
    "DR Congo":"الكونغو الديمقراطية","Congo DR":"الكونغو الديمقراطية",
    "England":"إنجلترا","Croatia":"كرواتيا","Ghana":"غانا","Panama":"بنما",
    "Uzbekistan":"أوزبكستان","Colombia":"كولومبيا",
}
 
# ترجمة أسماء المراحل
ROUND_AR = {
    "Round of 32":"دور الـ32","Round of 16":"دور الـ16",
    "Quarter-final":"ربع النهائي","Semi-final":"نصف النهائي",
    "Match for third place":"تحديد المركز الثالث","Final":"النهائي",
}
 
# ---------- أعلام المنتخبات (emoji) ----------
FLAG = {
    "Mexico":"🇲🇽","South Africa":"🇿🇦","South Korea":"🇰🇷",
    "Czech Republic":"🇨🇿","Czechia":"🇨🇿","Canada":"🇨🇦",
    "Bosnia and Herzegovina":"🇧🇦","Bosnia-Herzegovina":"🇧🇦","Bosnia & Herzegovina":"🇧🇦",
    "United States":"🇺🇸","USA":"🇺🇸","Paraguay":"🇵🇾","Qatar":"🇶🇦",
    "Switzerland":"🇨🇭","Brazil":"🇧🇷","Morocco":"🇲🇦","Haiti":"🇭🇹",
    "Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","Australia":"🇦🇺","Turkey":"🇹🇷","Türkiye":"🇹🇷","Turkiye":"🇹🇷",
    "Germany":"🇩🇪","Curacao":"🇨🇼","Curaçao":"🇨🇼","Netherlands":"🇳🇱","Japan":"🇯🇵",
    "Ivory Coast":"🇨🇮","Côte d'Ivoire":"🇨🇮","Ecuador":"🇪🇨","Sweden":"🇸🇪","Tunisia":"🇹🇳",
    "Spain":"🇪🇸","Cape Verde":"🇨🇻","Cabo Verde":"🇨🇻","Belgium":"🇧🇪","Egypt":"🇪🇬",
    "Saudi Arabia":"🇸🇦","Uruguay":"🇺🇾","Iran":"🇮🇷","IR Iran":"🇮🇷","New Zealand":"🇳🇿",
    "France":"🇫🇷","Senegal":"🇸🇳","Iraq":"🇮🇶","Norway":"🇳🇴","Argentina":"🇦🇷",
    "Algeria":"🇩🇿","Austria":"🇦🇹","Jordan":"🇯🇴","Portugal":"🇵🇹",
    "DR Congo":"🇨🇩","Congo DR":"🇨🇩","England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Croatia":"🇭🇷","Ghana":"🇬🇭",
    "Panama":"🇵🇦","Uzbekistan":"🇺🇿","Colombia":"🇨🇴",
}
 
def flag(t):
    return FLAG.get((t or "").strip(), "")
 
def team_name(t):
    """اسم المنتخب بالإنجليزي مع علمه (يرجع الرمز كما هو لو إقصائيات: W91...)"""
    t = (t or "").strip()
    fl = FLAG.get(t, "")
    return f"{fl} {t}".strip() if fl else t
 
def round_label(r, group):
    if r and r.startswith("Matchday"):
        return group or "Group Stage"
    return ROUND_AR.get(r, r) + (f" / {r}" if r in ROUND_AR else "")
 
def parse_dt(date_str, time_str):
    """يحوّل 'YYYY-MM-DD' + 'HH:MM UTC-6' إلى datetime بتوقيت UTC."""
    m = re.match(r"(\d{1,2}):(\d{2})\s*UTC([+-]\d{1,2})", time_str.strip())
    hh, mm, off = int(m.group(1)), int(m.group(2)), int(m.group(3))
    local = datetime(*map(int, date_str.split("-")), hh, mm,
                     tzinfo=timezone(timedelta(hours=off)))
    return local.astimezone(timezone.utc)
 
def fold(line):
    raw = line.encode("utf-8"); out = []
    while len(raw) > 73:
        out.append(raw[:73].decode("utf-8","ignore")); raw = b" " + raw[73:]
    out.append(raw.decode("utf-8","ignore"))
    return "\r\n".join(out)
 
def main():
    h2h = load_h2h()
    # المصدر الرئيسي: نعيد المحاولة حتى 3 مرات قبل الاستسلام
    data = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(SOURCE, headers={"User-Agent": "worldcup-cal"})
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            print(f"محاولة {attempt+1} لتحميل المصدر الرئيسي فشلت:", e)
            if attempt == 2:
                raise
    matches = data["matches"]
 
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    L = ["BEGIN:VCALENDAR","VERSION:2.0",
         "PRODID:-//WorldCup2026//Friends Auto Calendar//EN",
         "CALSCALE:GREGORIAN","METHOD:PUBLISH",
         "X-WR-CALNAME:Omar's World Cup / مونديال عمر ⚽",
         "X-WR-TIMEZONE:UTC",
         "X-WR-CALDESC:FIFA World Cup 2026 - auto-updated schedule & results",
         "REFRESH-INTERVAL;VALUE=DURATION:PT6H","X-PUBLISHED-TTL:PT6H"]
 
    for i, m in enumerate(matches, 1):
        start = parse_dt(m["date"], m["time"])
        end = start + timedelta(minutes=120)
        # ثبات الـ UID: نعتمد رقم المباراة الرسمي إن وُجد، وإلا الترتيب
        uid_key = m.get("num", i)
        uid = f"wc2026-m{uid_key:03d}@worldcup-friends"
 
        t1, t2 = team_name(m.get("team1","TBD")), team_name(m.get("team2","TBD"))
        stage = round_label(m.get("round",""), m.get("group"))
        ground = m.get("ground","")
        group = m.get("group","")
 
        # ---- النتيجة (من score.ft) ----
        score = m.get("score") or {}
        ft = score.get("ft")
        played = bool(ft and len(ft) == 2)
 
        if played:
            summary = f"{t1} {ft[0]} - {ft[1]} {t2}"
        else:
            summary = f"{t1} vs {t2}"
 
        # ---- بناء الوصف ----
        desc_lines = []
 
        if played:
            ht = score.get("ht")
            if ht and len(ht) == 2:
                desc_lines.append(f"HT: {ht[0]} - {ht[1]}")
 
            def scorers(goals):
                out = []
                for g in goals or []:
                    nm = g.get("name","").strip()
                    mn = g.get("minute","")
                    if nm:
                        out.append(f"{nm} {mn}'" if mn else nm)
                return out
 
            g1 = scorers(m.get("goals1"))
            g2 = scorers(m.get("goals2"))
            if g1:
                desc_lines.append(f"⚽ {m.get('team1','')}: " + "، ".join(g1))
            if g2:
                desc_lines.append(f"⚽ {m.get('team2','')}: " + "، ".join(g2))
        else:
            # مباراة لم تُلعب بعد: نضيف السجل التاريخي (للمنتخبات المعروفة فقط)
            raw1, raw2 = m.get("team1",""), m.get("team2","")
            # نتجاهل رموز الإقصائيات (W91, Winner Group A...)
            known = raw1 in AR and raw2 in AR
            if known:
                desc_lines.append(h2h_text(raw1, raw2, h2h))
 
        desc_lines.append(f"{stage} | FIFA World Cup 2026")
        desc = "\\n".join(desc_lines)
 
        L += ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{now}",
              f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
              f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
              fold(f"SUMMARY:{summary}"), fold(f"DESCRIPTION:{desc}")]
        if ground:
            L.append(fold(f"LOCATION:{ground}"))
        L += ["STATUS:CONFIRMED","TRANSP:TRANSPARENT","END:VEVENT"]
 
    L.append("END:VCALENDAR")
    with open(OUT,"w",encoding="utf-8") as f:
        f.write("\r\n".join(L) + "\r\n")
    print(f"OK: wrote {len(matches)} matches to {OUT}")
 
if __name__ == "__main__":
    main()
 
