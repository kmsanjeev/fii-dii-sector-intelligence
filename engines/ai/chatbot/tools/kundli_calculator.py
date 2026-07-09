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

try:
    from engines.ai.chatbot.tools.kundli_interpreter import generate_life_readings as _gen_life
except Exception:
    _gen_life = None  # graceful fallback if import fails

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

# ── Panchang constants ────────────────────────────────────────────────────────
TITHI_NAMES = [
    "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi",
    "Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi",
    "Trayodashi","Chaturdashi","Purnima",                              # Shukla 1-15
    "Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi",
    "Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi",
    "Trayodashi","Chaturdashi","Amavasya",                             # Krishna 16-30
]
YOGA_NAMES = [
    "Vishkambha","Priti","Ayushman","Saubhagya","Shobhana","Atiganda",
    "Sukarma","Dhriti","Shula","Ganda","Vriddhi","Dhruva","Vyaghata",
    "Harshana","Vajra","Siddhi","Vyatipata","Variyana","Parigha",
    "Shiva","Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti",
]
KARANA_MOVABLE = ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti"]
VARA_DAYS  = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
VARA_LORDS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
# Navamsa (D9) first-navamsa sign index by rashi element
_D9_START  = {0:0, 1:9, 2:6, 3:3, 4:0, 5:9, 6:6, 7:3, 8:0, 9:9, 10:6, 11:3}

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
    "nalanda":(25.1369,85.4415),"nalanda district":(25.1369,85.4415),
    "rajgir":(25.0269,85.4205),"bodh gaya":(24.6959,84.9914),
    "gaya":(24.7955,84.9994),"muzaffarpur":(26.1197,85.3910),
    "bhagalpur":(25.2425,86.9842),"darbhanga":(26.1542,85.8918),
    "purnia":(25.7771,87.4753),"ara":(25.5561,84.6564),
    "begusarai":(25.4182,86.1272),"chapra":(25.7831,84.7478),
    "katihar":(25.5478,87.5678),"samastipur":(25.8726,85.7778),
    "hajipur":(25.6837,85.2085),
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


# ── Lal Kitab Farmans (upaya remedies by planet) ─────────────────────────────
_LAL_KITAB: dict[str, dict] = {
    "Sun":     {"weak":["Donate wheat, copper or jaggery to the poor on Sundays",
                        "Offer Surya Arghya (water) daily at sunrise facing east",
                        "Feed monkeys or a red cow with jaggery on Sundays"],
                "h":{6:"Avoid ego; worship Sun deity and superiors with respect",
                     8:"Donate copper items on Sundays; stay away from alcohol",
                     12:"Help the visually impaired; donate to hospitals on Sundays"}},
    "Moon":    {"weak":["Feed crows or fish with rice and milk every Monday",
                        "Keep a small silver item (coin or ring) near head while sleeping",
                        "Offer white flowers or milk to the Moon on Mondays"],
                "h":{6:"Respect mother; serve cows and women on Mondays",
                     8:"Float milk in a river on Monday; keep silver in wallet",
                     12:"Donate white items to elderly women on Mondays"}},
    "Mars":    {"weak":["Feed sweet chapati (with jaggery) to dogs on Tuesdays",
                        "Donate red lentils (masoor dal) and copper on Tuesdays",
                        "Plant red flowers at home; keep a red cloth in the house"],
                "h":{1:"Donate red items on Tuesday; control anger consciously",
                     2:"Feed animals before eating your own meals daily",
                     4:"Plant a pomegranate tree at your home",
                     7:"Observe fast on Tuesdays; worship Lord Hanuman",
                     8:"Offer sindoor to Hanuman every Tuesday morning",
                     12:"Donate blood; feed red-coloured food to cows on Tuesdays"}},
    "Mercury": {"weak":["Feed green vegetables or grass to cows on Wednesdays",
                        "Donate green moong dal or green cloth on Wednesdays",
                        "Keep a green emerald-coloured object in your workspace"],
                "h":{}},
    "Jupiter": {"weak":["Donate yellow items (turmeric, chickpeas, cloth) on Thursdays",
                        "Apply tilak of turmeric or sandalwood on forehead on Thursdays",
                        "Respect your Guru, teachers, father and all elder figures"],
                "h":{6:"Donate yellow items to teachers; touch the feet of Guru",
                     8:"Never accept bribes or unethical money; stay principled",
                     12:"Donate to ashrams, temples or spiritual institutions"}},
    "Venus":   {"weak":["Donate white items (sugar, rice, white cloth) on Fridays",
                        "Donate to women's charities or provide for young girls on Friday",
                        "Serve your spouse or mother with unconditional devotion"],
                "h":{}},
    "Saturn":  {"weak":["Feed mustard oil and black sesame (til) to crows on Saturdays",
                        "Donate black cloth and urad dal to the needy on Saturdays",
                        "Serve the elderly, poor, disabled or homeless people selflessly",
                        "Pour mustard oil at the base of a peepal tree on Saturdays"],
                "h":{1:"Donate shoes or slippers to the poor on Saturday",
                     4:"Keep or feed stray black dogs; plant a peepal tree near home",
                     7:"Serve your spouse selflessly; dissolve ego in relationships"}},
    "Rahu":    {"weak":["Feed ants with sugar or wheat flour every day",
                        "Keep a multi-coloured blanket in the home",
                        "Donate a coconut wrapped in a cloth to a temple"],
                "h":{}},
    "Ketu":    {"weak":["Donate spotted or multi-coloured blankets to the poor",
                        "Feed stray dogs and cats every day",
                        "Perform Pitru Tarpan (ancestor water offering) on Amavasya"],
                "h":{}},
}


def _get_city_coords(place: str) -> Optional[tuple[float, float]]:
    """Built-in dict -> learned cache -> Nominatim (global, online).
    Falls back through the chain silently; None only if every tier fails."""
    try:
        from engines.ai.chatbot.tools.geocoder import resolve_city
        hit = resolve_city(place, builtin=CITY_COORDS)
        if hit:
            return (hit[0], hit[1])
    except Exception:
        # Geocoder must never break kundli generation -- fall through
        pass
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
    all_ads: list[dict] = []
    maha_pl = cur_maha["planet"]
    maha_start = datetime.strptime(cur_maha["start_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    maha_idx = DASHA_SEQUENCE.index(maha_pl)

    ad_cur = maha_start
    for i in range(len(DASHA_SEQUENCE)):
        ad_pl  = DASHA_SEQUENCE[(maha_idx + i) % len(DASHA_SEQUENCE)]
        ad_yrs = DASHA_YEARS[maha_pl] * DASHA_YEARS[ad_pl] / TOTAL_DASHA_YEARS
        ad_end = ad_cur + timedelta(days=ad_yrs * 365.25)
        is_now = ad_cur <= today <= ad_end
        all_ads.append({
            "planet":     ad_pl,
            "start_date": ad_cur.strftime("%Y-%m-%d"),
            "end_date":   ad_end.strftime("%Y-%m-%d"),
            "years":      round(ad_yrs, 2),
            "is_current": is_now,
        })
        if is_now and not antardasha:
            antardasha = {"planet": ad_pl,
                          "start_date": ad_cur.strftime("%Y-%m-%d"),
                          "end_date":   ad_end.strftime("%Y-%m-%d")}
            pa_cur = ad_cur
            ad_i   = DASHA_SEQUENCE.index(ad_pl)
            for j in range(len(DASHA_SEQUENCE)):
                pa_pl  = DASHA_SEQUENCE[(ad_i + j) % len(DASHA_SEQUENCE)]
                pa_yrs = DASHA_YEARS[maha_pl] * DASHA_YEARS[ad_pl] * DASHA_YEARS[pa_pl] / (TOTAL_DASHA_YEARS ** 2)
                pa_end = pa_cur + timedelta(days=pa_yrs * 365.25)
                if pa_cur <= today <= pa_end:
                    pratyantardasha = {"planet": pa_pl,
                                       "start_date": pa_cur.strftime("%Y-%m-%d"),
                                       "end_date":   pa_end.strftime("%Y-%m-%d")}
                    break
                pa_cur = pa_end
        ad_cur = ad_end

    return {
        "mahadasha":        cur_maha,
        "antardasha":       antardasha,
        "pratyantardasha":  pratyantardasha,
        "all_mahadashas":   all_mds,
        "all_antardashas":  all_ads,
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


# ── All-house significations ──────────────────────────────────────────────────
_HOUSE_SIG = {
    1:  "Self, personality, health, overall life direction",
    2:  "Wealth, savings, speech, family, food, right eye",
    3:  "Siblings, courage, communication, short journeys, hands",
    4:  "Mother, home, property, vehicles, education, chest",
    5:  "Children, intelligence, creativity, speculation, past life merits",
    6:  "Enemies, debts, diseases, litigation, service, maternal uncle",
    7:  "Spouse, partnerships, business, foreign journeys, lower abdomen",
    8:  "Longevity, obstacles, inheritance, transformation, hidden knowledge",
    9:  "Father, fortune, higher education, religion, guru, long journeys",
    10: "Career, reputation, authority, government, public image, knees",
    11: "Income, gains, elder siblings, social networks, hopes and desires",
    12: "Losses, moksha, foreign lands, expenses, bed pleasures, left eye",
}

# ── Financial house significations (subset) ───────────────────────────────────
_FH_SIG = {
    2: "Wealth, savings, liquid assets, speech, family",
    5: "Speculation, creativity, intelligence, children, investments",
    8: "Inheritance, transformation, hidden wealth, longevity, occult",
    10: "Career, public status, authority, reputation, father",
    11: "Income, gains, elder siblings, large networks, desires fulfilled",
}


# ── Vedic special aspects (drishti) ──────────────────────────────────────────
# All planets cast 7th house aspect (full); Mars+Jupiter+Saturn have special
_SPECIAL_ASPECTS = {
    "Mars":    [4, 7, 8],
    "Jupiter": [5, 7, 9],
    "Saturn":  [3, 7, 10],
}
_DEFAULT_ASPECTS = [7]

def _compute_drishti(planets: dict) -> list[dict]:
    """Compute Vedic graha drishti (planetary aspects) for all 9 planets."""
    aspects = []
    for pname, pdata in planets.items():
        ph = pdata.get("house")
        if ph is None:
            continue
        houses_aspected = _SPECIAL_ASPECTS.get(pname, _DEFAULT_ASPECTS)
        aspected_houses = [(ph + offset - 1) % 12 + 1 for offset in houses_aspected]
        aspected_planets = [
            tgt for tgt, tdata in planets.items()
            if tdata.get("house") in aspected_houses and tgt != pname
        ]
        aspects.append({
            "planet":           pname,
            "from_house":       ph,
            "aspects_houses":   aspected_houses,
            "aspected_planets": aspected_planets,
        })
    return aspects


def _all_12_houses(planets: dict, lagna_idx: int) -> dict:
    """Build all 12 house dicts (whole-sign)."""
    houses = {}
    for hnum in range(1, 13):
        sign_idx = (lagna_idx + hnum - 1) % 12
        sign = SIGNS[sign_idx]
        lord = SIGN_RULERS[sign]
        pl   = planets.get(lord, {})
        occ  = [p for p, d in planets.items() if d.get("house") == hnum]
        dg   = pl.get("dignity", "neutral")
        malefic_occ = any(p in ("Saturn","Mars","Rahu","Ketu") for p in occ)
        benefic_occ = any(p in ("Jupiter","Venus") for p in occ)
        strength = ("strong" if dg in ("exalted","own_sign","moolatrikona") or benefic_occ
                    else "weak"   if dg == "debilitated" or malefic_occ
                    else "moderate")
        houses[f"H{hnum}"] = {
            "house":          hnum,
            "sign":           sign,
            "lord":           lord,
            "lord_house":     pl.get("house"),
            "lord_dignity":   dg,
            "occupants":      occ,
            "strength":       strength,
            "signification":  _HOUSE_SIG[hnum],
        }
    return houses


def _dasha_interpretation(planet: str, dignity: str) -> str:
    """Return a short interpretation of a dasha planet based on its natal dignity."""
    positive = dignity in ("exalted","own_sign","moolatrikona","friendly")
    themes = {
        "Sun":     "authority, government service, leadership, vitality",
        "Moon":    "emotions, mother, property, mental peace, public dealings",
        "Mars":    "energy, real estate, siblings, courage, surgery",
        "Mercury": "business, communication, education, trade, writing",
        "Jupiter": "wisdom, wealth, children, spirituality, expansion",
        "Venus":   "luxury, relationships, arts, vehicles, finances",
        "Saturn":  "career, discipline, delays, labour, long-term gains",
        "Rahu":    "ambition, technology, foreign elements, sudden changes",
        "Ketu":    "spirituality, detachment, research, losses, moksha",
    }
    th = themes.get(planet, "general life themes")
    tone = "favourable period for" if positive else "karmic test period — challenges in"
    return f"{tone} {th}"


def _build_formatted_report(
    entity: dict, birth_details: dict, lagna: dict, planets: dict,
    dasha: dict, all_houses: dict, fh: dict, yogas: list,
    drishti: list, bull: list, bear: list, narr: str,
    score: float, action: str,
    panchang: Optional[dict] = None,
    doshas: Optional[list] = None,
    vargas: Optional[dict] = None,
    remedies: Optional[list] = None,
) -> str:
    """Build a complete pre-formatted Vedic Kundli report as text."""
    lines: list[str] = []
    sep  = "=" * 52
    dash = "-" * 52

    lines += [sep, "   VEDIC NATAL CHART  (JYOTISH KUNDLI)", "   Lahiri Ayanamsha | Whole-Sign Houses | Vimshottari Dasha", sep, ""]

    # Birth details
    lines += ["BIRTH DETAILS", dash]
    lines.append(f"  Date        : {entity.get('inception_date','')}  ({datetime.strptime(entity['inception_date'],'%Y-%m-%d').strftime('%d %B %Y') if entity.get('inception_date') else ''})")
    lines.append(f"  Time (Local): {entity.get('inception_time','')} (UTC{'+' if entity.get('timezone_offset_hours',5.5)>=0 else ''}{entity.get('timezone_offset_hours',5.5):.1f}){'  [approximate — Ascendant may vary]' if entity.get('time_approximate') else ''}")
    lines.append(f"  Place       : {entity.get('place','')}  ({entity.get('latitude',0):.4f}N, {entity.get('longitude',0):.4f}E)")
    lines.append(f"  UTC Time    : {birth_details.get('utc_datetime','')}")
    lines.append(f"  Ayanamsha   : {birth_details.get('ayanamsha',0):.4f} deg ({birth_details.get('ayanamsha_type','')})")
    lines.append("")

    # Panchang
    if panchang:
        lines += ["PANCHANG  (VEDIC ALMANAC -- 5 LIMBS)", dash]
        t  = panchang.get("tithi",    {})
        nk = panchang.get("nakshatra",{})
        yg = panchang.get("yoga",     {})
        kr = panchang.get("karana",   {})
        vr = panchang.get("vara",     {})
        lines.append(f"  Tithi     : {t.get('number','')} - {t.get('name','')}  [{t.get('phase','')}]")
        lines.append(f"  Nakshatra : {nk.get('name','')} Pada {nk.get('pada','')}  (lord: {nk.get('lord','')})")
        lines.append(f"  Yoga      : {yg.get('number','')} - {yg.get('name','')}")
        lines.append(f"  Karana    : {kr.get('number','')} - {kr.get('name','')}  ({kr.get('type','')})")
        lines.append(f"  Vara      : {vr.get('name','')}  (lord: {vr.get('lord','')})")
        lines.append("")

    # Lagna
    lines += ["LAGNA (ASCENDANT)", dash]
    lagna_lord = lagna.get("lord","")
    ll_data = planets.get(lagna_lord, {})
    lines.append(f"  Sign   : {lagna.get('sign','')} ({_vedic_name(lagna.get('sign',''))})")
    lines.append(f"  Degree : {lagna.get('degree',0):.2f} deg  in  {lagna.get('sign','')}")
    lines.append(f"  Lord   : {lagna_lord}  — H{ll_data.get('house','?')}, {ll_data.get('sign','')}, {ll_data.get('dignity','neutral')}")
    lines.append("")

    # Planetary table
    lines += ["PLANETARY POSITIONS  (GRAHA STHITI)", dash]
    lines.append(f"  {'Planet':<10}  {'Sign':<14}  {'Deg':>6}  H   {'Nakshatra':<20}  P  {'Dignity':<14}  R")
    lines.append(f"  {'-'*10}  {'-'*14}  {'-'*6}  --  {'-'*20}  -  {'-'*14}  -")
    ORDER = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    for pname in ORDER:
        pd = planets.get(pname)
        if pd is None:
            continue
        retro = "R" if pd.get("retrograde") else "-"
        vname = _vedic_name(pd.get("sign",""))
        sign_str = f"{pd.get('sign','')} ({vname})" if vname else pd.get("sign","")
        lines.append(
            f"  {pname:<10}  {sign_str:<14}  {pd.get('degree',0):>6.2f}  {pd.get('house',''):>2}  "
            f"{pd.get('nakshatra',''):<20}  {pd.get('pada','')}  {pd.get('dignity','neutral'):<14}  {retro}"
        )
    lines.append("  Key: H = House (Whole Sign)  |  P = Pada  |  R = Retrograde")
    lines.append("")

    # Dasha
    lines += ["VIMSHOTTARI DASHA", dash]
    maha = dasha.get("mahadasha") or {}
    ant  = dasha.get("antardasha") or {}
    prat = dasha.get("pratyantardasha") or {}
    if maha:
        mp = maha.get("planet","")
        mp_dg = planets.get(mp,{}).get("dignity","neutral")
        mp_h  = planets.get(mp,{}).get("house","?")
        lines.append(f"  Mahadasha      : {mp:<10} ends {maha.get('end_date','')[:10]}  [H{mp_h}, {mp_dg}]")
        lines.append(f"  Interpretation : {_dasha_interpretation(mp, mp_dg)}")
    if ant:
        ap = ant.get("planet","")
        ap_dg = planets.get(ap,{}).get("dignity","neutral")
        lines.append(f"  Antardasha     : {ap:<10} ends {ant.get('end_date','')[:10]}  [{ap_dg}]")
    if prat:
        pp = prat.get("planet","")
        lines.append(f"  Pratyantardasha: {pp:<10} ends {prat.get('end_date','')[:10]}")
    lines.append("")
    lines.append("  Mahadasha Timeline (120-year Vimshottari cycle):")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for m in (dasha.get("all_mahadashas") or [])[:12]:
        marker = "  <-- NOW" if m.get("start_date","") <= today_str <= m.get("end_date","") else ""
        lines.append(f"    {m.get('planet',''):<10} {m.get('start_date','')[:10]} to {m.get('end_date','')[:10]}{marker}")
    lines.append("")

    # Antardasha timeline within current Mahadasha
    all_ads = dasha.get("all_antardashas") or []
    if all_ads and maha:
        lines.append(f"  Antardasha Timeline (within {maha.get('planet','')} Mahadasha):")
        lines.append(f"  {'Antardasha':<12}  {'Start':<12}  {'End':<12}  {'Yrs':>5}")
        lines.append(f"  {'-'*12}  {'-'*12}  {'-'*12}  {'-'*5}")
        for ad in all_ads:
            marker = "  <-- NOW" if ad.get("is_current") else ""
            lines.append(f"  {ad.get('planet',''):<12}  {ad.get('start_date','')[:10]}  {ad.get('end_date','')[:10]}  {ad.get('years',0):>5.2f}{marker}")
        lines.append("")

    # Yogas
    lines += ["ACTIVE YOGAS", dash]
    pos_yogas = [y for y in yogas if y.get("score",0) >= 0]
    neg_yogas = [y for y in yogas if y.get("score",0) < 0]
    if pos_yogas:
        lines.append("  Positive Yogas:")
        for y in pos_yogas:
            lines.append(f"    + {y.get('name',''):<30}  [{y.get('signal','')}]")
            lines.append(f"      Effect: {y.get('effect','')}")
    if neg_yogas:
        lines.append("  Challenging Yogas:")
        for y in neg_yogas:
            lines.append(f"    - {y.get('name',''):<30}  [{y.get('signal','')}]")
            lines.append(f"      Effect: {y.get('effect','')}")
    if not yogas:
        lines.append("  No major yogas detected in this chart.")
    lines.append("")

    # Doshas
    lines += ["DOSHAS  (AFFLICTIONS & WARNINGS)", dash]
    if doshas:
        for d in doshas:
            sev = d.get("severity","").upper()
            lines.append(f"  [{sev}]  {d.get('name','')}  (Planets: {d.get('planets','')} in H{d.get('house','')})")
            lines.append(f"    {d.get('description','')}")
        lines.append("")
        lines.append("  Dosha Remedies (see Lal Kitab Farmans section below for full list):")
        for d in doshas:
            lines.append(f"    {d.get('name','')} -> {d.get('remedy','')}")
    else:
        lines.append("  No classic doshas detected in this chart.")
    lines.append("")

    # All 12 houses
    lines += ["ALL 12 HOUSES  (BHAVA ANALYSIS)", dash]
    lines.append(f"  {'H':<3}  {'Sign':<14}  {'Lord':<8}  {'Lord-H':<7}  {'Occupants':<24}  {'Strength':<8}  Signification")
    lines.append(f"  {'-'*3}  {'-'*14}  {'-'*8}  {'-'*7}  {'-'*24}  {'-'*8}  {'-'*20}")
    for hnum in range(1, 13):
        hd = all_houses.get(f"H{hnum}", {})
        occ_str = ", ".join(hd.get("occupants",[]))[:22] or "--"
        lord_h  = str(hd.get("lord_house") or "?")
        lines.append(
            f"  {hnum:<3}  {hd.get('sign',''):<14}  {hd.get('lord',''):<8}  "
            f"H{lord_h:<6}  {occ_str:<24}  {hd.get('strength',''):<8}  {hd.get('signification','')[:40]}"
        )
    lines.append("")

    # Financial houses (detailed)
    lines += ["FINANCIAL HOUSES  (ARTHA BHAVAS)", dash]
    FH_NAMES = {
        "2H":"2nd House — WEALTH (Dhana Bhava)",
        "5H":"5th House — SPECULATION & INVESTMENTS (Putra Bhava)",
        "8H":"8th House — INHERITANCE & HIDDEN WEALTH (Ayu Bhava)",
        "10H":"10th House — CAREER & STATUS (Karma Bhava)",
        "11H":"11th House — INCOME & GAINS (Labha Bhava)",
    }
    for key, title in FH_NAMES.items():
        hd = fh.get(key, {})
        if not hd:
            continue
        occ  = ", ".join(hd.get("occupants",[])) or "No occupants"
        lord = hd.get("lord","")
        lh   = hd.get("lord_house")
        ldg  = hd.get("lord_dignity","neutral")
        lines.append(f"  {title}")
        lines.append(f"    Sign       : {hd.get('sign','')}   |   Lord: {lord} (H{lh}, {ldg})")
        lines.append(f"    Occupants  : {occ}")
        lines.append(f"    Strength   : {hd.get('strength','moderate').upper()}")
        lines.append(f"    Signif.    : {hd.get('signification','')}")
        lines.append("")

    # Divisional charts
    if vargas:
        lines += ["DIVISIONAL CHARTS  (VARGA)", dash]
        d9 = vargas.get("d9_navamsa", [])
        d10 = vargas.get("d10_dasamsa", [])
        if d9:
            lines.append("  D9 - NAVAMSA  (Soul's Journey | Marriage | Dharma | Spiritual Path)")
            lines.append(f"  {'Planet':<10}  {'Rashi (D1)':<15}  {'Navamsa Sign (D9)':<18}  Lord")
            lines.append(f"  {'-'*10}  {'-'*15}  {'-'*18}  {'-'*8}")
            for r in d9:
                lines.append(f"  {r.get('planet',''):<10}  {r.get('rashi',''):<15}  {r.get('navamsa_sign',''):<18}  {r.get('navamsa_lord','')}")
            lines.append("")
        if d10:
            lines.append("  D10 - DASAMSA  (Career | Public Status | Professional Life)")
            lines.append(f"  {'Planet':<10}  {'Rashi (D1)':<15}  {'Dasamsa Sign (D10)':<18}  Lord")
            lines.append(f"  {'-'*10}  {'-'*15}  {'-'*18}  {'-'*8}")
            for r in d10:
                lines.append(f"  {r.get('planet',''):<10}  {r.get('rashi',''):<15}  {r.get('dasamsa_sign',''):<18}  {r.get('dasamsa_lord','')}")
            lines.append("")

    # Drishti
    lines += ["PLANETARY ASPECTS  (VEDIC DRISHTI)", dash]
    for asp in drishti:
        pname = asp.get("planet","")
        ph    = asp.get("from_house","?")
        aspH  = asp.get("aspects_houses",[])
        aspP  = asp.get("aspected_planets",[])
        aspH_str = ", ".join(f"H{h}" for h in aspH)
        aspP_str = ", ".join(aspP) if aspP else "--"
        lines.append(f"  {pname:<10} (H{ph}) aspects {aspH_str:<20}  targets: {aspP_str}")
    lines.append("")

    # Bullish / bearish factors
    lines += ["KEY LIFE FACTORS", dash]
    lines.append("  POSITIVE:")
    for f in bull:
        lines.append(f"    + {f}")
    lines.append("  CHALLENGING:")
    for f in bear:
        lines.append(f"    - {f}")
    lines.append("")

    # Summary
    lines += ["OVERALL ASSESSMENT", dash]
    lines.append(f"  Chart Score  : {score:+.1f}  ({action})")
    if maha:
        mp = maha.get("planet","")
        mp_dg = planets.get(mp,{}).get("dignity","neutral")
        lines.append(f"  Current Dasha: {mp} Mahadasha [{mp_dg}] — {_dasha_interpretation(mp, mp_dg)}")
    lines.append("")
    # Wrap narrative at ~70 chars
    words = narr.split()
    line_buf = "  "
    for word in words:
        if len(line_buf) + len(word) + 1 > 72:
            lines.append(line_buf)
            line_buf = "  " + word
        else:
            line_buf += (" " if line_buf != "  " else "") + word
    if line_buf.strip():
        lines.append(line_buf)
    lines.append("")
    # Lal Kitab Remedies
    if remedies:
        lines += ["LAL KITAB REMEDIES  (FARMANS / UPAYAS)", dash]
        lines.append("  Practical remedies for chart afflictions (Lal Kitab tradition, 1939-1952).")
        lines.append("  These are charitable deeds, not superstition -- most involve giving or serving.")
        lines.append("")
        for idx, rem in enumerate(remedies, 1):
            lines.append(f"  [{idx}] {rem.get('reason','')}")
            for farman in rem.get("farmans", []):
                lines.append(f"      - {farman}")
            lines.append("")
        lines.append("  Ethical note: Remedies are positive actions (charity, service, worship).")
        lines.append("  They supplement -- never replace -- professional and practical guidance.")
        lines.append("")

    lines.append("  NOTE: Chart computed via PyEphem + Lahiri ayanamsha. Dignities are")
    lines.append("  calculated (not paraphrased). For major decisions, consult a Jyotishi.")
    lines.append(sep)

    return "\n".join(lines)


def _compute_panchang(sun_sid_lon: float, moon_sid_lon: float, birth_local: datetime) -> dict:
    """Compute the five Panchang limbs at birth: Tithi, Nakshatra, Yoga, Karana, Vara.
    birth_local must be the local (IST or timezone-aware) birth datetime so that Vara reflects the local date."""
    diff = (moon_sid_lon - sun_sid_lon) % 360.0

    # Tithi: every 12 degrees of Moon-Sun elongation
    tithi_idx = int(diff / 12.0)               # 0-29
    tithi_num = tithi_idx + 1                  # 1-30
    tithi_name = TITHI_NAMES[tithi_idx]
    tithi_phase = "Shukla (waxing)" if tithi_num <= 15 else "Krishna (waning)"

    # Moon Nakshatra (already in planets, but re-derive for panchang completeness)
    moon_nak = _nakshatra_info(moon_sid_lon)

    # Yoga: (Sun + Moon) combined longitude / 13.333 deg per yoga
    yoga_lon = (sun_sid_lon + moon_sid_lon) % 360.0
    yoga_idx = int(yoga_lon * 27.0 / 360.0) % 27  # 0-26
    yoga_name = YOGA_NAMES[yoga_idx]

    # Karana: every 6 degrees of elongation
    karana_num = int(diff / 6.0) + 1           # 1-60
    if karana_num == 1:
        karana_name, karana_type = "Kimstughna", "fixed"
    elif 2 <= karana_num <= 57:
        karana_name = KARANA_MOVABLE[(karana_num - 2) % 7]
        karana_type = "movable"
    elif karana_num == 58:
        karana_name, karana_type = "Shakuni", "fixed"
    elif karana_num == 59:
        karana_name, karana_type = "Chatushpada", "fixed"
    else:
        karana_name, karana_type = "Naga", "fixed"

    # Vara (weekday): use LOCAL birth date (not UTC). Python weekday 0=Mon...6=Sun → Sun=0 via (wd+1)%7
    vara_idx  = (birth_local.weekday() + 1) % 7
    vara_name = VARA_DAYS[vara_idx]
    vara_lord = VARA_LORDS[vara_idx]

    return {
        "tithi":     {"number": tithi_num, "name": tithi_name, "phase": tithi_phase},
        "nakshatra": {"name": moon_nak["name"], "pada": moon_nak["pada"], "lord": moon_nak["lord"]},
        "yoga":      {"number": yoga_idx + 1, "name": yoga_name},
        "karana":    {"number": karana_num, "name": karana_name, "type": karana_type},
        "vara":      {"name": vara_name, "lord": vara_lord},
    }


def _doshas(planets: dict, lagna_idx: int) -> list[dict]:
    """Detect classic Vedic doshas: Manglik, Shani, Guru-Chandal, Surya-Chandal, Shani-Chandra."""
    out = []
    mars   = planets.get("Mars",    {})
    saturn = planets.get("Saturn",  {})
    moon   = planets.get("Moon",    {})
    rahu   = planets.get("Rahu",    {})
    jupiter= planets.get("Jupiter", {})
    sun    = planets.get("Sun",     {})

    mars_h   = mars.get("house",    0)
    sat_h    = saturn.get("house",  0)
    moon_h   = moon.get("house",    0)
    rahu_h   = rahu.get("house",    0)
    jup_h    = jupiter.get("house", 0)
    sun_h    = sun.get("house",     0)

    # Manglik Dosha (Kuja Dosha): Mars in H1, H2, H4, H7, H8, H12
    if mars_h in (1, 2, 4, 7, 8, 12):
        out.append({
            "name": "Manglik Dosha (Kuja Dosha)",
            "planets": "Mars",
            "house": mars_h,
            "description": (
                f"Mars in H{mars_h} — traditionally inauspicious for marriage; "
                "can cause friction in partnerships unless partner is also Manglik."
            ),
            "severity": "moderate",
            "remedy": "Marry someone who is also Manglik; perform Mangal path on Tuesdays; donate red lentils",
        })

    # Shani Dosha: Saturn in H1, H4, H7 from Lagna
    if sat_h in (1, 4, 7):
        out.append({
            "name": "Shani Dosha",
            "planets": "Saturn",
            "house": sat_h,
            "description": (
                f"Saturn in H{sat_h} (Kendra from Lagna) — delays, obstacles, slow rewards; "
                "strong discipline develops through adversity."
            ),
            "severity": "moderate",
            "remedy": "Worship Lord Shiva on Saturdays; donate sesame oil and black items on Saturday",
        })

    # Shani Dosha from Moon: Saturn in 4th or 7th from Moon (if not already captured above)
    if moon_h and sat_h:
        sat_from_moon = (sat_h - moon_h) % 12 + 1
        if sat_from_moon in (4, 7) and sat_h not in (1, 4, 7):
            out.append({
                "name": "Shani Dosha (from Moon)",
                "planets": "Saturn",
                "house": sat_h,
                "description": (
                    f"Saturn is H{sat_from_moon} from Moon — emotional restrictions, "
                    "delays in domestic happiness, strained relationship with mother."
                ),
                "severity": "mild",
                "remedy": "Chant Shani Stotra on Saturdays; feed crows and fish on Saturdays",
            })

    # Surya Chandal Dosha: Sun + Rahu in same house
    if sun_h and rahu_h and sun_h == rahu_h:
        out.append({
            "name": "Surya Chandal Dosha",
            "planets": "Sun + Rahu",
            "house": sun_h,
            "description": (
                f"Sun and Rahu conjunct in H{sun_h} — ego conflicts with ambition; "
                "challenges with authority figures, father; unconventional self-expression."
            ),
            "severity": "moderate",
            "remedy": "Donate wheat and copper on Sundays; offer Surya Arghya daily at sunrise",
        })

    # Guru Chandal Dosha: Jupiter + Rahu in same house
    if jup_h and rahu_h and jup_h == rahu_h:
        out.append({
            "name": "Guru Chandal Dosha",
            "planets": "Jupiter + Rahu",
            "house": jup_h,
            "description": (
                f"Jupiter and Rahu conjunct in H{jup_h} — wisdom distorted by worldly desire; "
                "ethical conflicts; unconventional beliefs or teachers in life."
            ),
            "severity": "significant",
            "remedy": "Donate yellow cloth and turmeric on Thursdays; respect all teachers sincerely",
        })

    # Shani-Chandra Yoga: Moon + Saturn in same house
    if moon_h and sat_h and moon_h == sat_h:
        out.append({
            "name": "Shani-Chandra Yoga",
            "planets": "Moon + Saturn",
            "house": moon_h,
            "description": (
                f"Moon and Saturn conjunct in H{moon_h} — emotional suppression, melancholy tendency, "
                "difficult early relationship with mother; develops stoic resilience over time."
            ),
            "severity": "moderate",
            "remedy": "Feed crows and black sesame on Saturdays; worship Lord Shiva on Mondays",
        })

    return out


def _navamsa_sign(sidereal_lon: float) -> str:
    """D9 Navamsa sign: each sign has 9 parts of 3d20m. Fire=start Aries, Earth=Capricorn, Air=Libra, Water=Cancer."""
    sign_idx    = int(sidereal_lon / 30.0) % 12
    deg_in_sign = sidereal_lon % 30.0
    navamsa_num = int(deg_in_sign * 9.0 / 30.0)   # 0-8
    return SIGNS[(_D9_START[sign_idx] + navamsa_num) % 12]


def _dasamsa_sign(sidereal_lon: float) -> str:
    """D10 Dasamsa sign: 10 parts of 3 deg each. Odd signs start from same; even from 9th sign."""
    sign_idx    = int(sidereal_lon / 30.0) % 12
    deg_in_sign = sidereal_lon % 30.0
    dasamsa_num = int(deg_in_sign / 3.0)           # 0-9
    start = sign_idx if sign_idx % 2 == 0 else (sign_idx + 8) % 12
    return SIGNS[(start + dasamsa_num) % 12]


def _compute_vargas(planets_out: dict) -> dict:
    """Compute D9 (Navamsa) and D10 (Dasamsa) for all 9 planets."""
    ORDER = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
    d9, d10 = [], []
    for pname in ORDER:
        pd = planets_out.get(pname)
        if pd is None:
            continue
        lon = pd.get("longitude", 0.0)
        d9_sign  = _navamsa_sign(lon)
        d10_sign = _dasamsa_sign(lon)
        d9.append({"planet": pname, "rashi": pd.get("sign",""), "navamsa_sign": d9_sign,
                   "navamsa_lord": SIGN_RULERS[d9_sign]})
        d10.append({"planet": pname, "rashi": pd.get("sign",""), "dasamsa_sign": d10_sign,
                    "dasamsa_lord": SIGN_RULERS[d10_sign]})
    return {"d9_navamsa": d9, "d10_dasamsa": d10}


def _lal_kitab_remedies(planets: dict, doshas: list, yogas: list) -> list[dict]:
    """Generate Lal Kitab farmans based on chart afflictions (debilitated/enemy planets, doshas, Kaal Sarp)."""
    out: list[dict] = []
    seen: set[str] = set()

    # Weak/debilitated/enemy planets
    for pname, pdata in planets.items():
        dignity = pdata.get("dignity", "neutral")
        house   = pdata.get("house", 0)
        if dignity not in ("debilitated", "enemy"):
            continue
        pl_rem = _LAL_KITAB.get(pname, {})
        farmans: list[str] = list(pl_rem.get("weak", []))[:2]
        house_rem = pl_rem.get("h", {}).get(house)
        if house_rem:
            farmans.append(house_rem)
        if farmans:
            key = f"{pname}_weak"
            if key not in seen:
                seen.add(key)
                out.append({
                    "planet": pname,
                    "reason": f"{pname} is {dignity} in H{house} ({pdata.get('sign','')})",
                    "farmans": farmans,
                })

    # Dosha-specific remedies
    for d in doshas:
        pnames = d.get("planets", "")
        key = f"dosha_{d.get('name','')}"
        if key not in seen:
            seen.add(key)
            rem = d.get("remedy", "")
            if rem:
                out.append({
                    "planet": pnames,
                    "reason": d.get("name", ""),
                    "farmans": [rem],
                })

    # Kaal Sarp Yoga
    for y in yogas:
        if y.get("name") == "Kaal Sarp Yoga" and "kaal_sarp" not in seen:
            seen.add("kaal_sarp")
            out.append({
                "planet": "Rahu/Ketu",
                "reason": "Kaal Sarp Yoga",
                "farmans": [
                    "Perform Kaal Sarp Dosh Nivaran Puja at a Shiva temple (especially Trimbakeshwar)",
                    "Offer milk and water on a Shiva lingam every Monday",
                    "Feed a snake idol or image with milk on Nag Panchami",
                    "Donate multi-coloured blankets and black items on Saturdays",
                ],
            })

    return out


def _vedic_name(sign: str) -> str:
    """Return Sanskrit rashi name for an English sign name."""
    MAP = {
        "Aries":"Mesha","Taurus":"Vrishabha","Gemini":"Mithuna","Cancer":"Karka",
        "Leo":"Simha","Virgo":"Kanya","Libra":"Tula","Scorpio":"Vrishchika",
        "Sagittarius":"Dhanu","Capricorn":"Makara","Aquarius":"Kumbha","Pisces":"Meena",
    }
    return MAP.get(sign, "")


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
                    f"City '{place_name}' could not be located (checked built-in list, "
                    f"local cache and online OpenStreetMap lookup -- the internet may be "
                    f"down or the spelling unusual). Please provide latitude and longitude "
                    f"directly. Example: latitude=28.6139, longitude=77.2090 for New Delhi."
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

    yogas         = _yogas(planets_out, lagna_idx)
    score, action = _astro_score_and_action(planets_out, dasha)
    bull, bear    = _factors(planets_out, dasha, fh)
    narr          = _narrative(lagna, planets_out, dasha, yogas, score, action)
    all_houses    = _all_12_houses(planets_out, lagna_idx)
    drishti       = _compute_drishti(planets_out)

    # New: Panchang, Doshas, Divisional Charts, Lal Kitab remedies
    sun_sid_lon   = planets_out.get("Sun",  {}).get("longitude", 0.0)
    moon_sid_lon  = planets_out.get("Moon", {}).get("longitude", 0.0)
    panchang      = _compute_panchang(sun_sid_lon, moon_sid_lon, birth_local)
    doshas        = _doshas(planets_out, lagna_idx)
    vargas        = _compute_vargas(planets_out)
    remedies      = _lal_kitab_remedies(planets_out, doshas, yogas)

    entity = {
        "type": "person",
        "inception_date": birth_date.strftime("%Y-%m-%d"),
        "inception_time": f"{birth_time.hour:02d}:{birth_time.minute:02d}:{birth_time.second:02d}",
        "place": place_name,
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "timezone_offset_hours": timezone_offset_hours,
        "time_approximate": time_approx,
    }
    birth_details = {
        "utc_datetime": birth_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "local_datetime": birth_local.strftime("%Y-%m-%d %H:%M:%S"),
        "ayanamsha": round(ayanamsha, 4),
        "ayanamsha_type": "Lahiri (Chitrapaksha)",
        "julian_date": round(jd, 4),
    }

    formatted_report = _build_formatted_report(
        entity, birth_details, lagna, planets_out, dasha,
        all_houses, fh, yogas, drishti, bull, bear, narr, score, action,
        panchang=panchang, doshas=doshas, vargas=vargas, remedies=remedies,
    )

    # Append comprehensive life readings (BPHS-based narratives for all life areas)
    if _gen_life is not None:
        try:
            _life_input = {
                "planets":    planets_out,
                "lagna":      lagna,
                "all_houses": all_houses,
                "dasha":      dasha,
                "yogas":      yogas,
            }
            life_block = _gen_life(_life_input)
            if life_block:
                formatted_report = formatted_report + "\n" + life_block
        except Exception:
            pass  # never let interpreter errors break the main report

    # Append plain-English Life Guide: good/bad periods, sade sati, summary (KU-2)
    try:
        from engines.ai.chatbot.tools.kundli_life_guide import build_life_guide
        now_utc = datetime.now(timezone.utc)
        now_trop = _compute_positions(now_utc)
        now_ayan = _lahiri_ayanamsha(ephem.julian_date(ephem.Date(now_utc.strftime("%Y/%m/%d %H:%M:%S"))))
        sat_sid  = _sidereal(now_trop["Saturn"]["lon"], now_ayan)
        transit_saturn_sign = _sign_of(sat_sid)
        guide_lines = build_life_guide(planets_out, lagna, dasha, remedies, transit_saturn_sign)
        if guide_lines:
            formatted_report = formatted_report + "\n" + "\n".join(guide_lines)
    except Exception:
        pass  # life guide must never break the main report

    return {
        "entity":            entity,
        "birth_details":     birth_details,
        "panchang":          panchang,
        "lagna":             lagna,
        "planets":           planets_out,
        "current_dasha":     dasha,
        "all_houses":        all_houses,
        "financial_houses":  fh,
        "planetary_aspects": drishti,
        "vargas":            vargas,
        "yogas":             yogas,
        "doshas":            doshas,
        "lal_kitab_remedies":remedies,
        "astro_score":       score,
        "astro_action":      action,
        "bullish_factors":   bull,
        "bearish_factors":   bear,
        "narrative":         narr,
        "formatted_report":  formatted_report,
    }
