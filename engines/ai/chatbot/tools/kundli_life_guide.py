"""
Kundli Life Guide -- Phase KU-2
Plain-English enrichment appended to the formatted Kundli report:

  1. GOOD & BAD PERIODS  -- next ~20 years of Vimshottari mahadashas rated
     EXCELLENT/GOOD/MIXED/CHALLENGING using classical rules a computer can
     apply: functional lordship for the person's lagna (trikona lords good,
     trik 6/8/12 lords difficult), the planet's dignity, its house, and its
     natural benefic/malefic character.
  2. SADE SATI STATUS    -- live check of transit Saturn vs natal Moon sign
     (12th/1st/2nd = Sade Sati) with phase and approximate end.
  3. WHAT THIS MEANS FOR YOU -- layman's summary: core nature, mind,
     current life chapter, best window, careful window, top simple remedies.

Everything is computed from the chart -- no external calls, no LLM.
All output is ASCII (Windows cp1252 console safe).
"""

from datetime import datetime, timezone

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
         "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

SIGN_LORDS = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}

# Everyday themes each planet's period tends to bring (plain English)
DASHA_THEMES = {
    "Sun":     "authority, government matters, father, recognition at work",
    "Moon":    "emotions, mother, home life, public dealings, travel",
    "Mars":    "energy, property, siblings, courage -- but also disputes if afflicted",
    "Mercury": "business, communication, studies, contracts, quick gains",
    "Jupiter": "growth, wisdom, children, wealth, spiritual progress",
    "Venus":   "marriage, comforts, vehicles, luxury, creative work",
    "Saturn":  "hard work, discipline, career through persistence, delays that teach",
    "Rahu":    "sudden changes, foreign connections, ambition, unconventional paths",
    "Ketu":    "detachment, spirituality, research -- material matters feel less rewarding",
}

PERIOD_ADVICE = {
    "EXCELLENT":   "Make your big moves here: new ventures, property, marriage, investments.",
    "GOOD":        "A supportive stretch. Progress comes with normal effort.",
    "MIXED":       "Ups and downs. Avoid big risks; consolidate what you have.",
    "CHALLENGING": "Go slow. Save money, avoid disputes and major new commitments; focus on health.",
}


def _houses_lorded(planet: str, lagna_sign: str) -> list[int]:
    """Which houses (1-12, whole sign) this planet lords for the given lagna."""
    if planet in ("Rahu", "Ketu"):
        return []
    lagna_idx = SIGNS.index(lagna_sign)
    return [
        ((SIGNS.index(sign) - lagna_idx) % 12) + 1
        for sign, lord in SIGN_LORDS.items() if lord == planet
    ]


_YOGAKARAKA_BY_LAGNA = {
    "Taurus": "Saturn", "Libra": "Saturn",
    "Cancer": "Mars",   "Leo":   "Mars",
    "Capricorn": "Venus", "Aquarius": "Venus",
}


def _rate_dasha(planet: str, planets: dict, lagna_sign: str) -> tuple[float, str, list[str]]:
    """Score a dasha lord's favourability. Returns (score, label, reasons)."""
    pd = planets.get(planet, {})
    score = 0.0
    reasons: list[str] = []

    # Yogakaraka: the single most productive planet for this lagna
    if _YOGAKARAKA_BY_LAGNA.get(lagna_sign) == planet:
        score += 2.0
        reasons.append("it is your chart's YOGAKARAKA -- the most productive planet for your lagna")

    # Functional lordship for this lagna
    lorded = _houses_lorded(planet, lagna_sign)
    for h in lorded:
        if h in (1, 5, 9):
            score += 1.5
            reasons.append(f"rules your house {h} (a lucky house for you)")
        elif h in (4, 7, 10):
            score += 0.5
        elif h in (6, 8, 12):
            score -= 1.5
            reasons.append(f"rules your house {h} (a difficult house for you)")
        elif h in (3, 11):
            score -= 0.5

    # Dignity in the birth chart
    dignity = str(pd.get("dignity", "neutral")).lower()
    if "exalt" in dignity:
        score += 2.0
        reasons.append("very strong (exalted) in your birth chart")
    elif "own" in dignity or "mool" in dignity:
        score += 1.5
        reasons.append("strong (in own sign) in your birth chart")
    elif "debilit" in dignity:
        score -= 2.0
        reasons.append("weak (debilitated) in your birth chart")

    # House the planet sits in
    house = pd.get("house")
    if house in (6, 8, 12):
        score -= 1.0
        reasons.append(f"sits in house {house} (a testing placement)")
    elif house in (1, 4, 5, 7, 9, 10):
        score += 0.75

    # Combustion mutes a period's delivery
    if pd.get("combust"):
        score -= 0.75
        reasons.append("it is combust (too close to the Sun) -- expression is muted")

    # Natural character
    if planet in NATURAL_BENEFICS:
        score += 0.5
    elif planet in ("Rahu", "Ketu"):
        score -= 0.75
    else:
        score -= 0.25

    if score >= 2.5:   label = "EXCELLENT"
    elif score >= 1.0: label = "GOOD"
    elif score >= -1.0: label = "MIXED"
    else:              label = "CHALLENGING"
    return score, label, reasons[:2]


def _sade_sati(natal_moon_sign: str, transit_saturn_sign: str) -> dict:
    """Sade Sati = transit Saturn in the 12th, 1st or 2nd sign from natal Moon."""
    moon_idx = SIGNS.index(natal_moon_sign)
    sat_idx  = SIGNS.index(transit_saturn_sign)
    rel = (sat_idx - moon_idx) % 12   # 0 = same sign as Moon
    if rel == 11:
        return {"active": True, "phase": "FIRST (rising)",
                "note": "beginning phase -- expenses and mental restlessness rise; roughly 7.5 years of Sade Sati ahead"}
    if rel == 0:
        return {"active": True, "phase": "SECOND (peak)",
                "note": "peak phase -- the most testing stretch for health, mind and finances; roughly 2.5 to 5 years remain"}
    if rel == 1:
        return {"active": True, "phase": "THIRD (setting)",
                "note": "final phase -- pressure gradually lifts; under 2.5 years remain"}
    # Small panoti: Saturn in 4th or 8th from Moon
    if rel in (3, 7):
        return {"active": False, "phase": f"DHAIYYA (small panoti, Saturn {rel+1}th from Moon)",
                "note": "a lighter 2.5-year Saturn test -- extra discipline needed, but far milder than Sade Sati"}
    return {"active": False, "phase": "NOT ACTIVE",
            "note": "no Saturn pressure on your Moon right now"}


def build_life_guide(
    planets: dict, lagna: dict, dasha: dict,
    remedies: list | None,
    transit_saturn_sign: str | None,
) -> list[str]:
    """Return report lines for the plain-English life guide sections."""
    lines: list[str] = []
    dashline = "-" * 52
    lagna_sign = lagna.get("sign", "")
    if lagna_sign not in SIGNS:
        return lines   # cannot rate without a valid lagna

    today = datetime.now(timezone.utc)

    # ── Section 1: good & bad periods ────────────────────────────────────────
    lines += ["GOOD & BAD PERIODS  (NEXT ~20 YEARS, PLAIN ENGLISH)", dashline]
    lines.append("  How to read this: each 'chapter' below is a planetary period")
    lines.append("  (mahadasha). The rating shows how friendly that planet is for")
    lines.append("  YOUR specific chart -- the same planet can be great for one")
    lines.append("  person and hard for another.")
    lines.append("")

    horizon = today.year + 20
    shown = 0
    for md in dasha.get("all_mahadashas", []):
        try:
            end   = datetime.strptime(md["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            start = datetime.strptime(md["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if end < today or start.year > horizon or shown >= 5:
            continue
        pl = md["planet"]
        score, label, reasons = _rate_dasha(pl, planets, lagna_sign)
        now_marker = "  <== you are here" if start <= today <= end else ""
        lines.append(f"  {start.strftime('%b %Y')} to {end.strftime('%b %Y')}  |  {pl} period  |  {label}{now_marker}")
        lines.append(f"    Life themes : {DASHA_THEMES.get(pl, '')}")
        if reasons:
            lines.append(f"    Why {label.lower():<11}: {'; '.join(reasons)}")
        lines.append(f"    Advice      : {PERIOD_ADVICE[label]}")
        lines.append("")
        shown += 1

    # Current antardasha mini-ratings (sub-chapters inside the current chapter)
    ads = [a for a in dasha.get("all_antardashas", [])
           if a.get("end_date", "") >= today.strftime("%Y-%m-%d")][:4]
    if ads:
        lines.append("  Sub-periods (antardasha) coming up inside the current chapter:")
        for a in ads:
            _, albl, _ = _rate_dasha(a["planet"], planets, lagna_sign)
            cur = "  <== current" if a.get("is_current") else ""
            lines.append(f"    {a['start_date'][:7]} to {a['end_date'][:7]}  {a['planet']:<8} {albl}{cur}")
        lines.append("")

    # ── Section 2: sade sati ─────────────────────────────────────────────────
    moon_sign = planets.get("Moon", {}).get("sign", "")
    if moon_sign in SIGNS and transit_saturn_sign in SIGNS:
        ss = _sade_sati(moon_sign, transit_saturn_sign)
        lines += ["SADE SATI CHECK  (SATURN'S 7.5-YEAR TEST)", dashline]
        lines.append("  Sade Sati is the roughly 7.5-year stretch when Saturn moves")
        lines.append("  over and around your Moon sign. It usually brings extra")
        lines.append("  responsibility, slower results and life lessons -- not doom.")
        lines.append("")
        lines.append(f"  Your Moon sign     : {moon_sign}")
        lines.append(f"  Saturn today       : {transit_saturn_sign}")
        lines.append(f"  Status             : {ss['phase']}")
        lines.append(f"  What it means      : {ss['note']}")
        if ss["active"]:
            lines.append("  Do's               : keep routines simple, honor commitments,")
            lines.append("                       serve elders, avoid shortcuts and new debt.")
        lines.append("")

    # ── Section 3: layman's summary ──────────────────────────────────────────
    lines += ["WHAT THIS MEANS FOR YOU  (SIMPLE SUMMARY)", dashline]
    ll = lagna.get("lord", "")
    lines.append(f"  Your outer self : {lagna_sign} rising -- how the world sees you and")
    lines.append(f"                    how you start things. Its planet ({ll}) sets your life's tone.")
    if moon_sign:
        nak = planets.get("Moon", {}).get("nakshatra", "")
        lines.append(f"  Your inner self : {moon_sign} Moon ({nak}) -- your instincts,")
        lines.append("                    emotional needs and what makes you feel secure.")
    maha = dasha.get("mahadasha") or {}
    if maha:
        mp = maha.get("planet", "")
        _, mlabel, _ = _rate_dasha(mp, planets, lagna_sign)
        lines.append(f"  Current chapter : {mp} period until {maha.get('end_date','')[:10]} -- rated {mlabel}")
        lines.append(f"                    for you. Focus: {DASHA_THEMES.get(mp,'')}.")

    # Best / careful windows from the rated mahadashas
    rated = []
    for md in dasha.get("all_mahadashas", []):
        try:
            end = datetime.strptime(md["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            start = datetime.strptime(md["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        if end < today or start.year > horizon:
            continue
        s, lbl, _ = _rate_dasha(md["planet"], planets, lagna_sign)
        rated.append((s, lbl, md))
    if rated:
        best  = max(rated, key=lambda r: r[0])
        worst = min(rated, key=lambda r: r[0])
        if best[1] in ("EXCELLENT", "GOOD"):
            lines.append(f"  Best window     : {best[2]['start_date'][:7]} to {best[2]['end_date'][:7]} "
                         f"({best[2]['planet']} period) -- plan major goals for this stretch.")
        else:
            lines.append(f"  Best window     : {best[2]['start_date'][:7]} to {best[2]['end_date'][:7]} "
                         f"({best[2]['planet']} period) -- the most workable stretch ahead; "
                         f"progress needs steady effort.")
        if worst[0] < 0 and worst[2] is not best[2]:
            lines.append(f"  Careful window  : {worst[2]['start_date'][:7]} to {worst[2]['end_date'][:7]} "
                         f"({worst[2]['planet']} period) -- keep savings, avoid big risks.")

    # Top remedies, restated simply
    if remedies:
        lines.append("")
        lines.append("  Three simple remedies that matter most for you:")
        count = 0
        for r in remedies:
            for tip in (r.get("remedies") or r.get("upaya") or [])[:1]:
                lines.append(f"    {count+1}. {tip}")
                count += 1
                break
            if count >= 3:
                break
        if count == 0:
            lines.append("    (none needed -- your chart carries no major affliction)")
    lines.append("")
    lines.append("  Note: astrology describes tendencies, not certainties. Use good")
    lines.append("  periods to act boldly and hard periods to prepare -- effort and")
    lines.append("  ethics always outrank planetary weather.")
    lines.append("")
    return lines
