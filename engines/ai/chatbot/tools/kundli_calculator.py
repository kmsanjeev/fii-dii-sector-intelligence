"""
Personal Kundli Calculator
Vedic (Jyotish) natal chart computation for human birth dates.
Uses PyEphem for planetary positions + Lahiri ayanamsha (sidereal zodiac).
Whole-sign house system. Vimshottari Dasha. 9 planets + Lagna.
"""

from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

import ephem

# ── Zodiac / Sign constants ───────────────────────────────────────────────────
SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
]
SIGN_RULERS = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}
EXALTATION = {
    "Sun":"Aries","Moon":"Taurus","Mercury":"Virgo","Venus":"Pisces",
    "Mars":"Capricorn","Jupiter":"Cancer","Saturn":"Libra",
    "Rahu":"Gemini","Ketu":"Sagittarius",
}
DEBILITATION = {
    "Sun":"Libra","Moon":"Scorpio","Mercury":"Pisces","Venus":"Virgo",
    "Mars":"Cancer","Jupiter":"Capricorn","Saturn":"Aries",
    "Rahu":"Sagittarius","Ketu":"Gemini",
}
MOOLATRIKONA = {
    "Sun":"Leo","Moon":"Taurus","Mercury":"Virgo","Venus":"Libra",
    "Mars":"Aries","Jupiter":"Sagittarius","Saturn":"Aquarius",
}
FRIENDLY = {
    "Sun":["Moon","Mars","Jupiter"],"Moon":["Sun","Mercury"],
    "Mars":["Sun","Moon","Jupiter"],"Mercury":["Sun","Venus"],
    "Jupiter":["Sun","Moon","Mars"],"Venus":["Mercury","Saturn"],
    "Saturn":["Mercury","Venus"],"Rahu":["Mercury","Venus","Saturn"],
    "Ketu":["Mercury","Venus","Saturn"],
}
ENEMY = {
    "Sun":["Venus","Saturn"],"Moon":[],"Mars":["Mercury"],
    "Mercury":["Moon"],"Jupiter":["Mercury","Venus"],
    "Venus":["Sun","Moon"],"Saturn":["Sun","Moon","Mars"],
    "Rahu":["Sun","Moon"],"Ketu":["Sun","Moon"],
}

# ── Nakshatra constants ───────────────────────────────────────────────────────
NAKSHATRAS = [
    "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
    "Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni",
    "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
    "Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha",
    "Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
]
NAKSHATRA_LORDS = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu",
    "Jupiter","Saturn","Mercury","Ketu","Venus","Sun",
    "Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
    "Ketu","Venus","Sun","Moon","Mars","Rahu",
    "Jupiter","Saturn","Mercury",
]

# ── Vimshottari Dasha ─────────────────────────────────────────────────────────
DASHA_YEARS = {
    "Ketu":7,"Venus":20,"Sun":6,"Moon":10,"Mars":7,
    "Rahu":18,"Jupiter":16,"Saturn":19,"Mercury":17,
}
DASHA_SEQUENCE = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"]
TOTAL_DASHA_YEARS = 120

# ── City coordinate lookup ────────────────────────────────────────────────────
CITY_COORDS: dict[str, tuple[float, float]] = {
    "mumbai":(19.0760,72.8777),"delhi":(28.6139,77.2090),"new delhi":(28.6139,77.2090),
    "bengaluru":(12.9716,77.5946),"bangalore":(12.9716,77.5946),
    "hyderabad":(17.3850,78.4867),"ahmedabad":(23.0225,72.5714),
    "chennai":(13.0827,80.2707),"kolkata":(22.5726,88.3639),
    "pune":(18.5204,73.8567),"jaipur":(26.9124,75.7873),
    "lucknow":(26.8467,80.9462),"surat":(21.1702,72.8311),
    "kanpur":(26.4499,80.3319),"nagpur":(21.1458,79.0882),
    "indore":(22.7196,75.8577),"patna":(25.5941,85.1376),
    "bhopal":(23.2599,77.4126),"agra":(27.1767,78.0081),
    "varanasi":(25.3176,82.9739),"kochi":(9.9312,76.2673),
    "cochin":(9.9312,76.2673),"thiruvananthapuram":(8.5241,76.9366),
    "trivandrum":(8.5241,76.9366),"coimbatore":(11.0168,76.9558),
    "mysuru":(12.2958,76.6394),"mysore":(12.2958,76.6394),
    "visakhapatnam":(17.6868,83.2185),"vizag":(17.6868,83.2185),
    "amritsar":(31.6340,74.8723),"chandigarh":(30.7333,76.7794),
    "guwahati":(26.1445,91.7362),"bhubaneswar":(20.2961,85.8245),
    "ranchi":(23.3441,85.3096),"dehradun":(30.3165,78.0322),
    "shimla":(31.1048,77.1734),"goa":(15.2993,74.1240),
    "panaji":(15.4909,73.8278),"jammu":(32.7266,74.8570),
    "srinagar":(34.0837,74.7973),"raipur":(21.2514,81.6296),
    "jodhpur":(26.2389,73.0243),"udaipur":(24.5854,73.7125),
    "meerut":(28.9845,77.7064),"allahabad":(25.4358,81.8463),
    "prayagraj":(25.4358,81.8463),"ghaziabad":(28.6692,77.4538),
    "faridabad":(28.4089,77.3178),"gurugram":(28.4595,77.0266),
    "gurgaon":(28.4595,77.0266),"noida":(28.5355,77.3910),
    "nashik":(19.9975,73.7898),"aurangabad":(19.8762,75.3433),
    "jabalpur":(23.1815,79.9864),"madurai":(9.9252,78.1198),
    "tirupati":(13.6288,79.4192),"vijayawada":(16.5062,80.6480),
    "ludhiana":(30.9010,75.8573),"jalandhar":(31.3260,75.5762),
    "mangaluru":(12.9141,74.8560),"mangalore":(12.9141,74.8560),
    "hubli":(15.3647,75.1240),"shillong":(25.5788,91.8933),
    "imphal":(24.8170,93.9368),"agartala":(23.8315,91.2868),
    "gangtok":(27.3389,88.6065),"itanagar":(27.0844,93.6053),
    "port blair":(11.6234,92.7265),
    # International
    "london":(51.5074,-0.1278),"new york":(40.7128,-74.0060),
    "dubai":(25.2048,55.2708),"singapore":(1.3521,103.8198),
    "toronto":(43.6532,-79.3832),"sydney":(-33.8688,151.2093),
    "hong kong":(22.3193,114.1694),"kuala lumpur":(3.1390,101.6869),
    "nairobi":(-1.2921,36.8219),"johannesburg":(-26.2041,28.0473),
    "doha":(25.2854,51.5310),"abu dhabi":(24.4539,54.3773),
    "riyadh":(24.6877,46.7219),"tokyo":(35.6762,139.6503),
    "beijing":(39.9042,116.4074),"shanghai":(31.2304,121.4737),
    "paris":(48.8566,2.3522),"frankfurt":(50.1109,8.6821),
    "zurich":(47.3769,8.5417),"amsterdam":(52.3676,4.9041),
    "vancouver":(49.2827,-123.1207),"san francisco":(37.7749,-122.4194),
    "los angeles":(34.0522,-118.2437),"chicago":(41.8781,-87.6298),
    "washington":(38.9072,-77.0369),
}


def _get_city_coords(place: str) -> Optional[tuple[float, float]]:
    key = place.strip().lower()
    if key in CITY_COORDS:
        return CITY_COORDS[key]
    for city, coords in CITY_COORDS.items():
        if key in city or city in key:
            return coords
    return None


def _lahiri_ayanamsha(jd: float) -> float:
    """Lahiri (Chitrapaksha) ayanamsha for a Julian Date. Returns degrees."""
    t = (jd - 2451545.0) / 36525.0  # Julian centuries from J2000
    return 23.85306 + t * 1.396


def _sidereal(tropical: float, ayanamsha: float) -> float:
    return (tropical - ayanamsha) % 360.0


def _sign_of(lon: float) -> str:
    return SIGNS[int(lon / 30) % 12]


def _deg_in_sign(lon: float) -> float:
    return lon % 30.0


def _nakshatra_info(sid_lon: float) -> dict:
    size = 360.0 / 27.0
    idx = int(sid_lon / size) % 27
    pada = int((sid_lon % size) / (size / 4)) + 1
    elapsed = (sid_lon % size) / size
    return {"name": NAKSHATRAS[idx], "lord": NAKSHATRA_LORDS[idx],
            "pada": pada, "idx": idx, "elapsed_fraction": elapsed}


def _dignity(planet: str, sign: str) -> str:
    if sign == EXALTATION.get(planet):
        return "exalted"
    if sign == DEBILITATION.get(planet):
        return "debilitated"
    if sign == MOOLATRIKONA.get(planet):
        return "moolatrikona"
    ruler = SIGN_RULERS.get(sign, "")
    if ruler == planet:
        return "own_sign"
    if ruler in FRIENDLY.get(planet, []):
        return "friendly"
    if ruler in ENEMY.get(planet, []):
        return "enemy"
    return "neutral"


def _compute_positions(dt_utc: datetime) -> dict[str, dict]:
    """Compute tropical planetary longitudes at dt_utc."""
    ed = ephem.Date(dt_utc.strftime("%Y/%m/%d %H:%M:%S"))
    ed_y = ephem.Date(ed - 1)
    bodies = {
        "Sun":ephem.Sun(),"Moon":ephem.Moon(),"Mercury":ephem.Mercury(),
        "Venus":ephem.Venus(),"Mars":ephem.Mars(),"Jupiter":ephem.Jupiter(),
        "Saturn":ephem.Saturn(),
    }
    out = {}
    for name, body in bodies.items():
        body.compute(ed)
        lon = math.degrees(ephem.Ecliptic(body, epoch=ephem.J2000).lon) % 360.0
        body.compute(ed_y)
        lon_y = math.degrees(ephem.Ecliptic(body, epoch=ephem.J2000).lon) % 360.0
        retro = ((lon - lon_y + 360.0) % 360.0) > 180.0
        out[name] = {"lon": lon, "retrograde": retro}

    # Rahu/Ketu — mean node formula (always retrograde)
    jd = ephem.julian_date(ed)
    t = (jd - 2451545.0) / 36525.0
    rahu = (125.0452 - 1934.136 * t) % 360.0
    if rahu < 0:
        rahu += 360.0
    out["Rahu"] = {"lon": rahu, "retrograde": True}
    out["Ketu"] = {"lon": (rahu + 180.0) % 360.0, "retrograde": True}
    return out


def _compute_lagna(dt_utc: datetime, lat: float, lon: float, ayanamsha: float) -> dict:
    """
    Compute sidereal Ascendant (Lagna) using LST + obliquity formula.
    Formula: tan(Asc) = cos(RAMC) / -(sin(eps)*tan(lat) + cos(eps)*sin(RAMC))
    """
    obs = ephem.Observer()
    obs.lat   = str(lat)
    obs.lon   = str(lon)
    obs.date  = ephem.Date(dt_utc.strftime("%Y/%m/%d %H:%M:%S"))
    obs.epoch = ephem.J2000
    obs.pressure = 0

    ramc_deg = math.degrees(float(obs.sidereal_time()))

    jd = ephem.julian_date(obs.date)
    t  = (jd - 2451545.0) / 36525.0
    eps_deg = 23.439291111 - 0.013004167 * t
    eps = math.radians(eps_deg)

    ramc = math.radians(ramc_deg)
    lat_r = math.radians(lat)

    # Standard Ascendant formula (Meeus Chapter 24)
    y = math.cos(ramc)
    x = -(math.sin(eps) * math.tan(lat_r) + math.cos(eps) * math.sin(ramc))
    asc_trop = math.degrees(math.atan2(y, x)) % 360.0

    asc_sid = _sidereal(asc_trop, ayanamsha)
    sign    = _sign_of(asc_sid)
    deg     = _deg_in_sign(asc_sid)
    lord    = SIGN_RULERS[sign]

    return {
        "sign": sign,
        "degree": round(deg, 2),
        "full_longitude": round(asc_sid, 4),
        "lord": lord,
    }


def _vimshottari(moon_nak_idx: int, elapsed: float, birth_utc: datetime) -> dict:
    """Compute Vimshottari dasha timeline from birth."""
    birth_lord = NAKSHATRA_LORDS[moon_nak_idx]
    lord_idx   = DASHA_SEQUENCE.index(birth_lord)

    all_mds = []
    cur = birth_utc

    # First dasha: remaining fraction
    remaining = (1.0 - elapsed) * DASHA_YEARS[birth_lord]
    end = cur + timedelta(days=remaining * 365.25)
    all_mds.append({"planet": birth_lord,
                    "start_date": cur.strftime("%Y-%m-%d"),
                    "end_date":   end.strftime("%Y-%m-%d"),
                    "years": round(remaining, 2)})
    cur = end

    # Full cycles × 2 to cover ~240 years
    for cycle in range(2):
        start_i = 1 if cycle == 0 else 0
        for i in range(start_i, len(DASHA_SEQUENCE)):
            idx = (lord_idx + i) % len(DASHA_SEQUENCE)
            pl  = DASHA_SEQUENCE[idx]
            yrs = DASHA_YEARS[pl]
            end = cur + timedelta(days=yrs * 365.25)
            all_mds.append({"planet": pl,
                            "start_date": cur.strftime("%Y-%m-%d"),
                            "end_date":   end.strftime("%Y-%m-%d"),
                            "years": yrs})
            cur = end

    today = datetime.now(timezone.utc)
    cur_maha = next(
        (m for m in all_mds
         if datetime.strptime(m["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc) <= today
         <= datetime.strptime(m["end_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)),
        all_mds[-1]
    )

    # Antardasha
    antardasha = {}
    pratyantardasha = {}
    maha_pl = cur_maha["planet"]
    maha_start = datetime.strptime(cur_maha["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    maha_idx = DASHA_SEQUENCE.index(maha_pl)

    ad_cur = maha_start
    for i in range(len(DASHA_SEQUENCE)):
        ad_pl = DASHA_SEQUENCE[(maha_idx + i) % len(DASHA_SEQUENCE)]
        ad_yrs = DASHA_YEARS[maha_pl] * DASHA_YEARS[ad_pl] / TOTAL_DASHA_YEARS
        ad_end = ad_cur + timedelta(days=ad_yrs * 365.25)
        if ad_cur <= today <= ad_end:
            antardasha = {"planet": ad_pl,
                          "start_date": ad_cur.strftime("%Y-%m-%d"),
                          "end_date":   ad_end.strftime("%Y-%m-%d")}
            # Pratyantardasha
            pa_cur = ad_cur
            ad_i = DASHA_SEQUENCE.index(ad_pl)
            for j in range(len(DASHA_SEQUENCE)):
                pa_pl = DASHA_SEQUENCE[(ad_i + j) % len(DASHA_SEQUENCE)]
                pa_yrs = DASHA_YEARS[maha_pl] * DASHA_YEARS[ad_pl] * DASHA_YEARS[pa_pl] / (TOTAL_DASHA_YEARS ** 2)
                pa_end = pa_cur + timedelta(days=pa_yrs * 365.25)
                if pa_cur <= today <= pa_end:
                    pratyantardasha = {"planet": pa_pl,
                                       "start_date": pa_cur.strftime("%Y-%m-%d"),
                                       "end_date":   pa_end.strftime("%Y-%m-%d")}
                    break
                pa_cur = pa_end
            break
        ad_cur = ad_end

    return {
        "mahadasha":       cur_maha,
        "antardasha":      antardasha,
        "pratyantardasha": pratyantardasha,
        "all_mahadashas":  all_mds,
    }


def _yogas(planets: dict, lagna_idx: int) -> list[dict]:
    out = []
    jup = planets.get("Jupiter", {})
    sat = planets.get("Saturn", {})
    ven = planets.get("Venus", {})
    mer = planets.get("Mercury", {})
    mars = planets.get("Mars", {})
    moon = planets.get("Moon", {})
    rahu = planets.get("Rahu", {})
    ketu = planets.get("Ketu", {})

    # Pancha Mahapurusha yogas
    for pl, name, effect in [
        ("Jupiter", "Hamsa Yoga",   "Wisdom, wealth, spiritual advancement"),
        ("Venus",   "Malavya Yoga", "Beauty, luxury, financial success"),
        ("Mercury", "Bhadra Yoga",  "Intellect, business acumen, analytical power"),
        ("Mars",    "Ruchaka Yoga", "Courage, leadership, physical strength"),
        ("Saturn",  "Sasa Yoga",    "Discipline, authority, long-term gains"),
    ]:
        p = planets.get(pl, {})
        if p.get("dignity") in ("own_sign","exalted","moolatrikona") and p.get("house") in [1,4,7,10]:
            out.append({"name": name, "effect": effect, "score": 18, "signal": "BUY"})

    # Gaja Kesari: Jupiter in kendra from Moon
    if jup and moon:
        rel = (jup.get("house",0) - moon.get("house",0)) % 12
        if rel in [0,3,6,9]:
            out.append({"name":"Gaja Kesari Yoga","effect":"Fame, wisdom, and lasting prosperity","score":15,"signal":"BUY"})

    # Dhana Yoga: lord of 2H and 11H connected
    s2  = SIGNS[(lagna_idx + 1) % 12]
    s11 = SIGNS[(lagna_idx + 10) % 12]
    l2  = SIGN_RULERS[s2]
    l11 = SIGN_RULERS[s11]
    p2  = planets.get(l2, {})
    p11 = planets.get(l11, {})
    if p2.get("house") == 11 or p11.get("house") == 2 or (l2 == l11):
        out.append({"name":"Dhana Yoga","effect":"Strong wealth accumulation potential","score":12,"signal":"BUY"})

    # Neecha Bhanga (debilitation cancellation)
    for pl, data in planets.items():
        if data.get("dignity") == "debilitated":
            debi_sign = DEBILITATION[pl]
            lord = SIGN_RULERS[debi_sign]
            p_lord = planets.get(lord, {})
            if p_lord.get("house") in [1,4,7,10]:
                out.append({"name":f"Neecha Bhanga ({pl})","effect":f"Debilitation cancelled — initial struggle gives exceptional results","score":8,"signal":"HOLD"})

    # Kaal Sarp: all planets between Rahu and Ketu
    if rahu and ketu:
        r_lon = rahu.get("longitude", 0)
        k_lon = ketu.get("longitude", 0)
        lo, hi = min(r_lon, k_lon), max(r_lon, k_lon)
        between = 0
        for pn in ["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn"]:
            lon = planets.get(pn, {}).get("longitude", -1)
            if lon < 0:
                continue
            if hi - lo < 180:
                if lo <= lon <= hi:
                    between += 1
            else:
                if lon <= lo or lon >= hi:
                    between += 1
        if between == 7:
            out.append({"name":"Kaal Sarp Yoga","effect":"Karmic challenges, delays, then sudden transformation","score":-12,"signal":"CAUTION"})

    # Kemadruma: Moon with no planet in adjacent houses
    if moon:
        mh = moon.get("house", 0)
        adj = [(mh - 2) % 12 + 1, mh % 12 + 1]
        has_adj = any(
            p.get("house") in adj
            for pn, p in planets.items()
            if pn not in ("Moon","Rahu","Ketu")
        )
        if not has_adj:
            out.append({"name":"Kemadruma Yoga","effect":"Emotional isolation tendency — needs conscious effort in relationships","score":-6,"signal":"CAUTION"})

    return out


def _astro_score_and_action(planets: dict, dasha: dict) -> tuple[float, str]:
    weights = {"exalted":15,"moolatrikona":12,"own_sign":10,"friendly":5,
               "neutral":0,"enemy":-5,"debilitated":-14}
    score = 0.0
    for pl in ["Jupiter","Venus","Mercury","Moon"]:
        score += weights.get(planets.get(pl,{}).get("dignity","neutral"), 0) * 1.2
    for pl in ["Saturn","Mars","Rahu","Ketu"]:
        d = planets.get(pl,{}).get("dignity","neutral")
        if d == "debilitated":
            score -= 8
        elif d in ("exalted","own_sign","moolatrikona"):
            score += 5

    maha_pl = (dasha.get("mahadasha") or {}).get("planet","")
    if maha_pl:
        d2 = planets.get(maha_pl,{}).get("dignity","neutral")
        score += weights.get(d2, 0) * 0.5

    score = max(-100, min(100, score * 1.4))
    if score >= 40:   action = "POSITIVE"
    elif score >= 15: action = "MODERATE"
    elif score >= -15:action = "NEUTRAL"
    elif score >= -40:action = "CHALLENGING"
    else:             action = "DIFFICULT"
    return round(score, 1), action


def _factors(planets: dict, dasha: dict, fh: dict) -> tuple[list, list]:
    bull, bear = [], []
    W = {"exalted":"exalted","moolatrikona":"moolatrikona",
         "own_sign":"in own sign","friendly":"in friendly sign"}

    for pl, lbl in [("Jupiter","Jupiter"),("Venus","Venus"),("Mercury","Mercury"),("Moon","Moon")]:
        p = planets.get(pl,{})
        dg = p.get("dignity","")
        if dg in W:
            bull.append(f"{pl} {W[dg]} in {p.get('sign','')} (H{p.get('house','')}) — favourable life force")
        elif dg == "debilitated":
            bear.append(f"{pl} debilitated in {p.get('sign','')} — weakened benefic influence")

    for pl in ["Saturn","Mars"]:
        p = planets.get(pl,{})
        if p.get("dignity") in ("exalted","own_sign"):
            bull.append(f"{pl} strong in {p.get('sign','')} — disciplined energy, structured gains")
        elif p.get("dignity") == "debilitated":
            bear.append(f"{pl} debilitated — delays, obstacles in career/health")
        if p.get("retrograde"):
            bear.append(f"{pl} retrograde — review past decisions; avoid major new commitments")

    mer = planets.get("Mercury",{})
    if mer.get("retrograde"):
        bear.append("Mercury retrograde at birth — revisiting ideas before committing; strong analytical ability")

    maha = dasha.get("mahadasha") or {}
    mpl = maha.get("planet","")
    if mpl:
        p = planets.get(mpl,{})
        dg = p.get("dignity","neutral")
        end = str(maha.get("end_date",""))[:7]
        if dg in ("exalted","own_sign","moolatrikona","friendly"):
            bull.append(f"{mpl} Mahadasha (until {end}) — dasha lord is strong; growth period")
        else:
            bear.append(f"{mpl} Mahadasha (until {end}) — karmic lessons; patience required")

    h11 = fh.get("11H",{})
    if h11.get("strength") == "strong":
        bull.append("11th house (income/gains) strong — fulfillment of desires, good income flow")
    elif h11.get("strength") == "weak":
        bear.append("11th house (income/gains) afflicted — income needs extra effort")

    h2 = fh.get("2H",{})
    if h2.get("strength") == "strong":
        bull.append("2nd house (wealth/savings) strong — natural wealth accumulation ability")
    elif h2.get("strength") == "weak":
        bear.append("2nd house afflicted — watch savings and speech; avoid speculation")

    return bull[:7], bear[:6]


def _narrative(lagna: dict, planets: dict, dasha: dict, yogas: list, score: float, action: str) -> str:
    lagna_sign = lagna.get("sign","")
    lord = lagna.get("lord","")
    p_lord = planets.get(lord, {})
    yoga_names = [y["name"] for y in yogas if y.get("score",0) > 0]
    maha = dasha.get("mahadasha") or {}
    ant  = dasha.get("antardasha") or {}

    dasha_str = maha.get("planet","")
    if ant.get("planet"):
        dasha_str += f"/{ant['planet']}"
    if maha.get("end_date"):
        dasha_str += f" (until {str(maha['end_date'])[:7]})"

    jup = planets.get("Jupiter",{})
    sat = planets.get("Saturn",{})

    n = (
        f"This is a {lagna_sign} Lagna (Ascendant) chart. "
        f"Lagna lord {lord} is in H{p_lord.get('house','?')} in {p_lord.get('sign','')} "
        f"({p_lord.get('dignity','neutral')} dignity). "
    )
    if yoga_names:
        n += f"Key positive yogas: {', '.join(yoga_names[:3])}. "
    n += (
        f"Currently running {dasha_str} Dasha. "
        f"Jupiter ({jup.get('dignity','neutral')} in {jup.get('sign','')}) and "
        f"Saturn ({sat.get('dignity','neutral')} in {sat.get('sign','')}) "
        f"shape financial karma. Chart score: {score:+.0f} ({action}). "
    )
    if score >= 30:
        n += "Overall strong chart — favourable planetary placements support growth and prosperity."
    elif score >= 0:
        n += "Balanced chart — opportunities present with karmic lessons; disciplined effort yields results."
    else:
        n += "Challenging chart — significant growth through adversity; spiritual development is accelerated."
    return n


# ── Financial house significations ────────────────────────────────────────────
_FH_SIG = {
    2: "Wealth, savings, liquid assets, speech, family",
    5: "Speculation, creativity, intelligence, children, investments",
    8: "Inheritance, transformation, hidden wealth, longevity, occult",
    10: "Career, public status, authority, reputation, father",
    11: "Income, gains, elder siblings, large networks, desires fulfilled",
}


def compute_personal_kundli(
    date_of_birth: str,
    time_of_birth: str,
    place_name: str,
    latitude:  Optional[float] = None,
    longitude: Optional[float] = None,
    timezone_offset_hours: float = 5.5,
) -> dict:
    """
    Compute a complete Vedic natal chart.

    Args:
        date_of_birth: "DD-MM-YYYY" or "YYYY-MM-DD"
        time_of_birth: "HH:MM" or "HH:MM:SS" (24-hr local time)
        place_name: City name for auto lat/lon lookup
        latitude/longitude: Override city lookup
        timezone_offset_hours: UTC offset (default 5.5 = IST)
    """
    # Parse date
    dob = date_of_birth.strip()
    if "-" in dob:
        parts = dob.split("-")
        fmt = "%Y-%m-%d" if len(parts[0]) == 4 else "%d-%m-%Y"
    elif "/" in dob:
        parts = dob.split("/")
        fmt = "%Y/%m/%d" if len(parts[0]) == 4 else "%d/%m/%Y"
    else:
        return {"error": f"Unrecognized date format: {dob}. Use DD-MM-YYYY or YYYY-MM-DD."}
    try:
        birth_date = datetime.strptime(dob, fmt)
    except ValueError as e:
        return {"error": f"Date parse failed: {e}"}

    # Parse time
    tob = time_of_birth.strip()
    time_approx = tob.lower() in ("unknown","","?","not known","nn")
    if time_approx:
        tob = "06:00:00"
    else:
        if tob.count(":") == 1:
            tob += ":00"

    try:
        birth_time = datetime.strptime(tob, "%H:%M:%S")
    except ValueError:
        return {"error": f"Unrecognized time format: {tob}. Use HH:MM (24-hour)."}

    # Combine → UTC
    tz = timezone(timedelta(hours=timezone_offset_hours))
    birth_local = birth_date.replace(
        hour=birth_time.hour, minute=birth_time.minute, second=birth_time.second,
        tzinfo=tz
    )
    birth_utc = birth_local.astimezone(timezone.utc)

    # Coordinates
    if latitude is None or longitude is None:
        coords = _get_city_coords(place_name)
        if coords is None:
            return {
                "error": (
                    f"City '{place_name}' not found. Please provide latitude and longitude. "
                    f"Example: latitude=28.6139, longitude=77.2090 for New Delhi."
                )
            }
        lat, lon = coords
    else:
        lat, lon = latitude, longitude

    # Compute positions
    try:
        trop = _compute_positions(birth_utc)
    except Exception as e:
        return {"error": f"Planetary computation failed: {e}"}

    jd = ephem.julian_date(ephem.Date(birth_utc.strftime("%Y/%m/%d %H:%M:%S")))
    ayanamsha = _lahiri_ayanamsha(jd)

    # Lagna
    try:
        lagna = _compute_lagna(birth_utc, lat, lon, ayanamsha)
    except Exception as e:
        return {"error": f"Ascendant computation failed: {e}"}

    lagna_idx = SIGNS.index(lagna["sign"])

    # Planets (sidereal)
    planets_out: dict[str, dict] = {}
    for name, tp in trop.items():
        sid = _sidereal(tp["lon"], ayanamsha)
        sign = _sign_of(sid)
        sign_idx = SIGNS.index(sign)
        house = (sign_idx - lagna_idx) % 12 + 1
        nak = _nakshatra_info(sid)
        dg  = _dignity(name, sign)
        planets_out[name] = {
            "longitude":     round(sid, 4),
            "sign":          sign,
            "degree":        round(_deg_in_sign(sid), 2),
            "house":         house,
            "nakshatra":     nak["name"],
            "nakshatra_lord":nak["lord"],
            "pada":          nak["pada"],
            "dignity":       dg,
            "retrograde":    tp["retrograde"],
        }

    # Moon nakshatra → dasha
    moon_sid = _sidereal(trop["Moon"]["lon"], ayanamsha)
    moon_nak = _nakshatra_info(moon_sid)
    dasha = _vimshottari(moon_nak["idx"], moon_nak["elapsed_fraction"], birth_utc)

    # Financial houses (whole sign)
    fh: dict[str, dict] = {}
    for hnum in [2, 5, 8, 10, 11]:
        sign_idx2 = (lagna_idx + hnum - 1) % 12
        sign2 = SIGNS[sign_idx2]
        lord2 = SIGN_RULERS[sign2]
        pl2   = planets_out.get(lord2, {})
        occ   = [p for p, d in planets_out.items() if d.get("house") == hnum]
        dg2   = pl2.get("dignity","neutral")
        strength = ("strong" if dg2 in ("exalted","own_sign","moolatrikona")
                    else "weak" if dg2 == "debilitated" or any(p in ["Saturn","Mars","Rahu","Ketu"] for p in occ)
                    else "moderate")
        fh[f"{hnum}H"] = {
            "sign": sign2, "lord": lord2,
            "lord_house": pl2.get("house"), "lord_dignity": dg2,
            "occupants": occ, "strength": strength,
            "signification": _FH_SIG[hnum],
        }

    yogas   = _yogas(planets_out, lagna_idx)
    score, action = _astro_score_and_action(planets_out, dasha)
    bull, bear = _factors(planets_out, dasha, fh)
    narr = _narrative(lagna, planets_out, dasha, yogas, score, action)

    return {
        "entity": {
            "type": "person",
            "inception_date": birth_date.strftime("%Y-%m-%d"),
            "inception_time": f"{birth_time.hour:02d}:{birth_time.minute:02d}:{birth_time.second:02d}",
            "place": place_name,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "timezone_offset_hours": timezone_offset_hours,
            "time_approximate": time_approx,
        },
        "birth_details": {
            "utc_datetime": birth_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
            "local_datetime": birth_local.strftime("%Y-%m-%d %H:%M:%S"),
            "ayanamsha": round(ayanamsha, 4),
            "ayanamsha_type": "Lahiri (Chitrapaksha)",
            "julian_date": round(jd, 4),
        },
        "lagna": lagna,
        "planets": planets_out,
        "current_dasha": dasha,
        "financial_houses": fh,
        "yogas": yogas,
        "astro_score": score,
        "astro_action": action,
        "bullish_factors": bull,
        "bearish_factors": bear,
        "narrative": narr,
    }
