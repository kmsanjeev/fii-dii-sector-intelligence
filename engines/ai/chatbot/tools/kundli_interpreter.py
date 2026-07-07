"""
Kundli Human Life Interpreter
Phase 14 (Kundli enhancement) -- Generates rich narrative life-area readings
from a computed Vedic natal chart dict (output of kundli_calculator.compute_personal_kundli).

Sources: BPHS, Phaladeepika, Saravali, Uttara Kalamrita, Lal Kitab.
"""

from __future__ import annotations
from typing import Optional

# ── Zodiac helpers (duplicated here to keep interpreter self-contained) ────────
_SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
]
_SIGN_LORDS = {
    "Aries":"Mars","Taurus":"Venus","Gemini":"Mercury","Cancer":"Moon",
    "Leo":"Sun","Virgo":"Mercury","Libra":"Venus","Scorpio":"Mars",
    "Sagittarius":"Jupiter","Capricorn":"Saturn","Aquarius":"Saturn","Pisces":"Jupiter",
}
_SIGN_IDX = {s: i for i, s in enumerate(_SIGNS)}

# ── BPHS / Phaladeepika / Saravali planet-in-house (108 entries) ──────────────
PLANET_IN_HOUSE = {
    "Sun": {
        1:  "Magnetic personality with strong ego, leadership ability, and robust vitality; may be proud or domineering; government and authority figures favour them.",
        2:  "Moderate wealth accumulation with pride in family lineage; speech is authoritative but can be harsh; father influences finances.",
        3:  "Courageous, self-reliant, enterprising; good relationship with younger siblings; excels in writing, communication, and short-distance ventures.",
        4:  "Comforts and property through effort; mother's health or happiness may fluctuate; interest in real estate; political ambitions rooted in homeland.",
        5:  "High intelligence and creative flair; struggles with firstborn or delays in children; speculative instinct; government or teaching career suits them.",
        6:  "Defeats enemies decisively; strong immunity and recovery from disease; excellent for government service, medicine, or military.",
        7:  "Marriage to a prominent or egoistic partner; business partnerships with authority figures; spouse may be in government or a leadership role.",
        8:  "Long life with hidden obstacles; interested in occult and mysteries; father or paternal side may face health setbacks; gains through inheritance.",
        9:  "Highly auspicious: fortunate, virtuous, and dharmic; father is influential and respected; pilgrimages, higher learning, and foreign travels are favoured.",
        10: "Exceptional career: government favour, authority positions, and public recognition; best placement for career -- natural executive, administrator, or politician.",
        11: "Steady income and social recognition; gains through government connections; many prominent friends; ambitions are fulfilled through network.",
        12: "Expenditure on prestige; foreign travel and spiritual inclinations; some eye health concerns; government expenses or loss of authority possible.",
    },
    "Moon": {
        1:  "Attractive, emotionally expressive, and popular; personality fluctuates with moods; strong bond with mother; good public appeal and empathy.",
        2:  "Fluctuating finances tied to emotional state; excellent memory; sweet, emotional speech; family-oriented wealth accumulation.",
        3:  "Mentally restless but imaginatively gifted; good relationship with siblings; frequent short travels; artistic and musical aptitude.",
        4:  "Deeply auspicious: happy home life, devoted mother, comforts, and vehicles; strong connection to birthplace; real estate gains likely.",
        5:  "Intelligent, creative, and emotionally attached to children; romantic nature; good memory and intuition; speculative ventures guided by instinct.",
        6:  "Digestive sensitivity and health fluctuations; many acquaintances but emotional enemies; service to others or healthcare career.",
        7:  "Charming, attractive spouse; emotionally dependent on partnership; business success through public-facing roles; many relationships possible.",
        8:  "Psychic sensitivity and deep emotions; longevity variable; inheritance from mother's side; drawn to occult and mystical subjects.",
        9:  "Deeply pious and fortunate; close to father in early life; religious mind; overseas connections or pilgrimages; intuitive teacher.",
        10: "Career in public life, politics, or healthcare; career changes are frequent; mother plays a pivotal role in professional journey; public popularity.",
        11: "Excellent for income: gains flow easily; many close friends, especially women; social popularity; fulfilment of desires through networks.",
        12: "Emotional reclusion and spiritual depth; foreign residence likely; sleep disturbances; subconscious is rich; charitable and compassionate.",
    },
    "Mars": {
        1:  "Athletic, bold, and action-oriented; short-tempered and accident-prone; strong physical constitution; Manglik dosha activates, affects marriage timing.",
        2:  "Harsh or direct speech; family disputes over money; aggressive financial behaviour; siblings may impact family wealth.",
        3:  "Outstanding courage and willpower; excellent relationship with siblings; competitive in all endeavours; military, sports, or technical skills.",
        4:  "Home conflicts and property disputes; mother's health may suffer; gains through land or construction.",
        5:  "Sharp, decisive intelligence; speculative and risk-taking in investments; challenges with firstborn; creative energy channelled into competitive pursuits.",
        6:  "Excellent placement: crushes enemies and disease; disciplined, high-energy service orientation; natural for military, police, or surgery.",
        7:  "Manglik dosha -- partner may be aggressive or early marriage leads to friction; spouse is driven and ambitious.",
        8:  "Risk of accidents, sudden events, and longevity challenges; strong occult interest; joint property conflicts; transformation through crisis.",
        9:  "Religious conflicts and dogmatic tendencies; fortune comes through effort, not luck; father-son tensions; overseas ventures require caution.",
        10: "Outstanding career in military, police, engineering, surgery, or real estate; aggressive ambition leads to authority positions.",
        11: "Income through competition and effort; driven social circle; gains in real estate, engineering, or sports.",
        12: "Expenditure through conflicts; secretive activities; foreign lands for work; hidden enemies.",
    },
    "Mercury": {
        1:  "Sharp intellect, eloquent communication, and youthful appearance; dual or adaptable nature; analytical and quick-witted; good in business.",
        2:  "Excellent financial intelligence and persuasive speech; family values education; skilled in trading.",
        3:  "Outstanding writing, journalism, and communication skills; very good sibling bonds; short-trip commerce.",
        4:  "Educated, analytical mother; happy, orderly home; real estate transactions handled skilfully; studies at home or homeland.",
        5:  "Exceptional intellect; scholarly and analytical children; stock market or financial acumen; creative writing; debates and teaching.",
        6:  "Health management through analysis; excellent medical or legal aptitude; defeats enemies through wit.",
        7:  "Intelligent, communicative spouse; business-minded partnerships; legal contracts and negotiations favour them.",
        8:  "Research aptitude and occult knowledge through analysis; inheritance through contracts; transformation via intellectual breakthroughs.",
        9:  "Learned teacher and philosopher; mastery of foreign languages; higher education is highly successful; dharmic through knowledge.",
        10: "Career in communication, IT, finance, journalism, or trade; analytical career success; multiple income sources.",
        11: "Income through trade, communication, or intellectual work; clever, analytical friends; gains from writing or media.",
        12: "Foreign travel for study or spiritual learning; expenses on communication tools; hidden intellectual abilities.",
    },
    "Jupiter": {
        1:  "Wise, benevolent, and optimistic; respected and well-regarded; tendency toward overweight in later life; natural teacher and counsellor.",
        2:  "Excellent wealth accumulation; learned, virtuous family; wise and eloquent speech; financial wisdom and generosity.",
        3:  "Philosophical communication; noble relationship with siblings; teaching through travel.",
        4:  "Happy, prosperous home; educated and pious mother; property and vehicles come naturally; excellent domestic life.",
        5:  "Outstanding children -- intelligent, devoted, successful; Gaja Kesari potential when Moon is in kendra; speculation guided by wisdom.",
        6:  "Enemies and debts may multiply initially but wisdom eventually overcomes rivals; service with generosity.",
        7:  "Excellent marriage: wise, virtuous spouse; legal and business success; fortune through partnerships; foreign collaborations.",
        8:  "Long life with wisdom; occult and philosophical knowledge; inheritance; transformation through spiritual growth.",
        9:  "Best house for Jupiter: highly fortunate, deeply religious and wise; guru or mentor influence is profound; overseas success.",
        10: "Career success in law, education, finance, religion, or administration; respected authority; government or corporate leadership.",
        11: "Great income and social expansion; excellent for financial gains; many influential and learned friends; wishes fulfilled.",
        12: "Spiritual liberation potential; foreign expansion; charitable donations; wisdom in solitude; ashram or retreat life.",
    },
    "Venus": {
        1:  "Attractive, charming, and artistic personality; pleasure-seeking and socially adept; appreciation of beauty, luxury, and refined environments.",
        2:  "Excellent wealth and financial comforts; melodious or charming speech; good family life; luxuries and fine possessions.",
        3:  "Artistic and aesthetic communication; creative writing and media; travel for pleasure; siblings may be artistic.",
        4:  "Beautifully decorated home; excellent comforts and vehicles; devoted and beautiful mother; real estate gains; domestic happiness.",
        5:  "Romantic and creative; artistic children; strong speculative intelligence; love of fine arts, music, and drama; love affairs are notable.",
        6:  "Competitive in beauty or service industry; enemies may be women or lovers; service with artistic excellence.",
        7:  "Excellent marriage -- beautiful, artistic, or wealthy spouse; business partnerships in luxury goods or arts; social harmony.",
        8:  "Sexual magnetism and deep intimacy; inheritance through spouse; joint property brings gains.",
        9:  "Fortune through arts and aesthetics; religious devotion with beauty; foreign travel for pleasure; dharma expressed through creativity.",
        10: "Career in arts, film, fashion, luxury goods, or diplomacy; respected for talent and charm; creative authority.",
        11: "Income through arts, entertainment, or luxury industry; social glamour and wealthy friends; desires fulfilled through beauty.",
        12: "Foreign pleasures and spiritual devotion; bedroom comforts; hidden relationships or secret love; expenses on luxury and pleasure.",
    },
    "Saturn": {
        1:  "Slow start in life but ultimately perseverant and successful; lean or bony constitution; disciplined and serious; longevity is generally strong.",
        2:  "Financial delays and hard-earned wealth; austere family environment; measured and careful speech; frugal and disciplined with money.",
        3:  "Great perseverance in all efforts; slow but methodical communication; hard-working siblings.",
        4:  "Early domestic hardships; mother's life may involve struggle; real estate gained through sustained effort; later in life, home becomes stable.",
        5:  "Delayed or fewer children; serious and disciplined intellect; karmic creativity; speculations only succeed with caution and research.",
        6:  "Excellent placement: destroys enemies and disease through sheer discipline; Karma Yoga; service-oriented career; systematic health management.",
        7:  "Delayed marriage; significant age gap with spouse; serious, responsible partner; marriage for duty and longevity.",
        8:  "Long life with chronic or recurring health challenges; delayed inheritance; occult discipline; transformation through endurance.",
        9:  "Strict religious discipline; father's life may involve hardship; foreign work travels; dharma through duty not joy.",
        10: "Strongest career placement: disciplined authority, late-blooming but lasting success; Karma Yoga (results match effort); government or corporate leader.",
        11: "Delayed but steady gains; serious and loyal friends; income through hard work and persistence; long-term financial goals achieved.",
        12: "Spiritual discipline and monastic inclinations; foreign service; expenses on necessities; isolation leads to liberation.",
    },
    "Rahu": {
        1:  "Unconventional personality with foreign or cross-cultural influences; ambitious, obsessive drive; unusual or distinctive appearance.",
        2:  "Obsessive focus on wealth; foreign income streams; unusual family dynamics; materialistic speech; gains through unconventional means.",
        3:  "Unusual courage and unorthodox communication; media or tech obsession; eccentric or foreign-influenced siblings; digital and disruptive ventures.",
        4:  "Real estate through unconventional means; foreign influence on home; restless in motherland; mother may be from different background.",
        5:  "Unusual children or childlessness; speculative obsession; unconventional creativity; karmic debts from past life influence progeny.",
        6:  "Favourable: enemies are confused or defeated; health through unconventional methods; reform-oriented service career.",
        7:  "Unconventional or foreign spouse; unusual partnerships; business with cross-border elements; karmic marriage relationship.",
        8:  "Occult obsession; sudden gains and losses; longevity variable; transformation through dramatic crises; research in hidden fields.",
        9:  "Foreign guru or unconventional belief systems; materialistic dharma; overseas education; fortune through foreign connections.",
        10: "Career in technology, foreign affairs, or unconventional fields; public ambition and drive; sudden rise in career.",
        11: "Great gains through unconventional or technological means; foreign friends and networks; ambitious income goals.",
        12: "Foreign residence; spiritual obsession; hidden expenses; liberation through confusion and dissolution of ego.",
    },
    "Ketu": {
        1:  "Spiritual, detached, and introspective personality; past-life wisdom informs current identity; health can be mysterious; moksha inclination.",
        2:  "Philosophical detachment from wealth; spiritual speech; family losses possible; karmic relationship with finances.",
        3:  "Detached or absent siblings; spiritual communication and mystical writing; courage drawn from detachment; past-life skill in communication.",
        4:  "Detached from home and mother; spiritual home life; property karma from past life; moves frequently or lives abroad.",
        5:  "Past-life intelligence manifest as brilliance; detachment from children; spiritual creativity; karmic speculation; children may be extraordinary.",
        6:  "Favourable: enemies and disease destroyed through karmic resolution; spiritual service; resolves past-life debts through health challenges.",
        7:  "Karmic spouse relationship; marriage for soul lessons; detached from partnerships; spiritual partnerships possible.",
        8:  "Occult mastery and deep metaphysical knowledge; detachment from death; moksha through transformation; sudden spiritual events.",
        9:  "Spiritual guru influence from past life; detachment from conventional dharma; past-life wisdom as philosophical guide.",
        10: "Detached from career outcomes; sudden career changes; spiritual authority; karmic work that serves humanity.",
        11: "Detachment from material gains; spiritual friends; past-life friendships rekindled; income through spiritual or humanitarian work.",
        12: "Best Ketu placement (Moksha Yoga): liberation, foreign spiritual connections; deep sleep and astral experiences.",
    },
}

# ── Lord-in-House interpretations (144 entries -- selected key ones) ──────────
LORD_IN_HOUSE = {
    1: {
        1:"Strong self-reliant personality; success through own initiative; life is self-directed.",
        2:"Wealth through personal effort; family-centric; early life financial focus.",
        3:"Courageous, communicative, self-promoter; frequent travel; close bond with siblings.",
        4:"Home and mother deeply important; emotional security drives life; real estate gains.",
        5:"Intelligent, creative personality; strong children bond; speculative and scholarly.",
        6:"Health challenges possible; competitive and service-oriented; good recovery power.",
        7:"Partnership-defined personality; marriage or business shapes identity; attractive and socially oriented.",
        8:"Hidden or mysterious personality; longevity concerns; interest in occult and transformation.",
        9:"Extremely fortunate: dharmic, philosophical, and well-travelled; father is a guide; blessed life.",
        10:"Strong career focus defines personality; authority and recognition are personal goals.",
        11:"Social and income-oriented personality; many friends; gains are important life metric.",
        12:"Spiritual or reclusive tendency; foreign residence likely; liberation is life theme.",
    },
    2: {
        1:"Wealth comes to native directly; family wealth attached to personal efforts.",
        2:"Excellent wealth: lord in own house strengthens financial house; family is wealthy and stable.",
        3:"Income through communication, writing, or media; siblings contribute to wealth.",
        4:"Wealth through real estate, vehicles, and mother; domestic income.",
        5:"Wealth through speculation, investments, or children's success; financial intelligence.",
        6:"Wealth through service, medical profession; financial challenges from debts possible.",
        7:"Wealth through spouse or business partnerships; marriage improves finances.",
        8:"Wealth through inheritance, spouse's family, or sudden gains; financial secrecy.",
        9:"Great fortune: wealth through luck, higher education, or father's legacy.",
        10:"Wealth through career and professional status; income tied to reputation.",
        11:"Best placement: wealth flows easily through gains, network, and elder siblings.",
        12:"Financial losses and expenditures; wealth goes to foreign places or charity.",
    },
    3: {
        1:"Courageous, communicative personality; siblings shape identity.",
        2:"Siblings contribute to family wealth; income through writing or short trade.",
        3:"Strong siblings and communication themes; excellent for media, writing, travel industry.",
        4:"Siblings connected to home or mother; real estate through sibling connections.",
        5:"Intelligent and courageous children; creative writing; communication leads to creativity.",
        6:"Sibling conflicts possible; competitive writing or media career; courage in service.",
        7:"Spouse met through sibling or communication; partnerships in media.",
        8:"Sibling-related sudden events; communication about hidden topics.",
        9:"Fortune through communication and short travel; siblings are philosophical.",
        10:"Career in communication, media, writing, or transport; siblings influence career.",
        11:"Gains through communication, siblings, or short trade.",
        12:"Communication leads to losses; siblings in foreign places.",
    },
    4: {
        1:"Strong attachment to home and mother; domestic personality; property ownership important.",
        2:"Family wealth through real estate and mother; home-based income.",
        3:"Mother's influence through communication; real estate education.",
        4:"Excellent: own house is strong; happy home life, good mother, property comes naturally.",
        5:"Mother is intelligent and creative; property through children's success.",
        6:"Home conflicts and mother's health issues; property disputes.",
        7:"Spouse from same hometown; home life tied to partnership; real estate through marriage.",
        8:"Hidden home matters; ancestral property through inheritance.",
        9:"Fortunate home life; educated, pious mother; property through luck.",
        10:"Career in real estate, construction, or government land; mother's influence on career.",
        11:"Gains from property and vehicles; mother supports income.",
        12:"Loss of home or living in foreign places; mother may be distant.",
    },
    5: {
        1:"Intelligent, creative personality; children are important; past-life karma is good.",
        2:"Financial intelligence and wise speech; children contribute to wealth.",
        3:"Creative communication and writing; children have communication skills.",
        4:"Happy children; educational focus in home; mother is intelligent.",
        5:"Excellent children and intelligence: lord in own house; strong Raja Yoga potential.",
        6:"Children may face health challenges; competitive use of intelligence.",
        7:"Love marriage possible: romance leads to union; spouse is intelligent.",
        8:"Children through difficult circumstances; occult intelligence; speculative losses possible.",
        9:"Exceptional Raja Yoga: great fortune through wisdom and children; luck is extraordinary.",
        10:"Career in education, arts, or investments; intelligent authority.",
        11:"Children bring gains; income through intelligence or speculation.",
        12:"Children in foreign lands; spiritual intelligence; meditation and hidden learning.",
    },
    6: {
        1:"Health and service define personality; competitive and hardworking.",
        2:"Wealth through service, medical, or legal profession.",
        3:"Siblings may be health-challenged or competitive; courage in facing disease.",
        4:"Domestic health issues; home environment has conflict; property through litigation.",
        5:"Children's health concerns; competitive intelligence; mental stress from speculation.",
        6:"Viparita Raja Yoga: enemies destroy each other; hardships lead to eventual victory.",
        7:"Spouse may be from service profession; marital health challenges.",
        8:"Serious health transformation; sudden illness possible.",
        9:"Fortunate despite enemies; disease healed through luck; foreign enemies.",
        10:"Career in medicine, law, military, or service sector.",
        11:"Gains through defeating competition or service.",
        12:"Viparita Raja Yoga: enemies destroy themselves; service leads to liberation.",
    },
    7: {
        1:"Marriage or partnership defines life; spouse-centric personality.",
        2:"Spouse contributes to family wealth; marriage improves finances.",
        3:"Spouse connected through sibling or communication; partnerships in media.",
        4:"Spouse from same hometown or shared background; home life tied to partnership.",
        5:"Love marriage or romance leading to marriage; intelligent, creative spouse.",
        6:"Marital conflicts and health challenges in marriage; divorce risk if lord is afflicted.",
        7:"Strong marriage house: lord in own sign; excellent for committed partnership.",
        8:"Sudden marriage events; spouse from wealthy family; marriage transforms both.",
        9:"Most auspicious marriage: fortunate, dharmic spouse; marriage brings great luck.",
        10:"Spouse advances career; marriage partner is a professional; business marriage.",
        11:"Marriage brings gains and fulfilment; friendship leads to love.",
        12:"Foreign spouse; spiritual or hidden relationship; spouse in foreign country.",
    },
    8: {
        1:"Mysterious, transformative personality; longevity concerns; hidden strengths.",
        2:"Wealth through inheritance or spouse's family; financial secrets.",
        3:"Sibling-related sudden events; communication about hidden topics.",
        4:"Ancestral property through inheritance; home transformation.",
        5:"Karmic children; occult intelligence; speculative losses possible.",
        6:"Viparita Raja Yoga: enemies and disease defeat each other.",
        7:"Spouse brings transformation; secret or sudden marriage; joint property complex.",
        8:"Long life with hidden obstacles: lord in own house; strong Viparita Raja potential.",
        9:"Philosophical understanding of transformation; father's health concerns.",
        10:"Career in research, occult, insurance, or investigation.",
        11:"Gains through inheritance or sudden windfalls.",
        12:"Viparita Raja Yoga: transformation leads to liberation.",
    },
    9: {
        1:"Highly fortunate and dharmic personality; father's blessings define life.",
        2:"Wealth through fortune and father's legacy; family traditions are dharmic.",
        3:"Fortune through communication and short travel; siblings are philosophical.",
        4:"Fortunate home life; dharmic mother; property through luck.",
        5:"Raja Yoga: 9th lord in 5th -- extraordinary fortune and intelligence.",
        6:"Dharmic service; fortune through defeating enemies; luck through hard work.",
        7:"Fortunate marriage: dharmic, pious, or foreign spouse.",
        8:"Philosophical understanding of transformation and death; fortune through inheritance.",
        9:"Extraordinary fortune: lord in own house; extremely lucky, religious, and learned.",
        10:"Dharma Karma Adhipati Yoga: outstanding career fortune.",
        11:"Fortune flows as gains; luck in income; friends are philosophical.",
        12:"Fortune in foreign lands or spiritual realms; dharma through renunciation.",
    },
    10: {
        1:"Career-focused personality; life centred on reputation and authority; self-made professional.",
        2:"Income directly from career; family supports profession; wealth through status.",
        3:"Career in communication, media, or travel industry.",
        4:"Career in real estate, homeland, or domestic industry; mother's influence on profession.",
        5:"Career in education, arts, or investments; professional creativity.",
        6:"Career in service, medicine, law, or military.",
        7:"Business partnerships define career; spouse in same profession.",
        8:"Career in research, investigation, insurance, or occult; sudden career changes.",
        9:"Dharma Karma Adhipati: outstanding career fortune; lucky professional life.",
        10:"Exceptional career: lord in own house; strong authority, leadership, and lasting reputation.",
        11:"Income matches career effort; professional gains are high.",
        12:"Career in foreign country or spiritual institution; behind-the-scenes authority.",
    },
    11: {
        1:"Income-oriented personality; social and network-driven; gains are central life theme.",
        2:"Excellent Dhana Yoga: gains flow into family wealth; elder siblings contribute.",
        3:"Gains through communication and short ventures; elder siblings are supportive.",
        4:"Income from property and domestic activities; friends support real estate gains.",
        5:"Income through speculation, investments, or children; creative gains.",
        6:"Income through service or defeating competition; gains despite enemies.",
        7:"Gains through business partnerships or spouse; income from marriage.",
        8:"Income through inheritance, insurance, or sudden events.",
        9:"Great fortune and income: Dhana-Dharma Yoga; lucky income streams.",
        10:"Career generates excellent income; professional gains high; authority brings wealth.",
        11:"Excellent: lord in own house; income flows consistently; elder siblings are successful.",
        12:"Expenditure exceeds income; friends in foreign places; gains through foreign networks.",
    },
    12: {
        1:"Spiritual or reclusive personality; expenses tied to self; foreign travel or residence.",
        2:"Family expenses and losses; wealth spent on spiritual matters; foreign income possible.",
        3:"Siblings in foreign places; communication expenses; short journeys for spiritual purposes.",
        4:"Home in foreign country; mother may be distant; property losses or expenses.",
        5:"Children born abroad; creative loss; past-life karma in creativity.",
        6:"Viparita Raja Yoga: enemies destroy losses; service in foreign lands.",
        7:"Foreign spouse; marriage involves sacrifice; partnerships in foreign country.",
        8:"Viparita Raja Yoga: losses destroy transformation obstacles; moksha through occult.",
        9:"Dharma through renunciation; foreign pilgrimage; spiritual learning overseas.",
        10:"Career in foreign country or spiritual institution; career involves isolation.",
        11:"Gains through foreign networks; income from abroad; expenses converted to gains.",
        12:"Strongest Moksha Yoga: lord in own house; life is spiritual and renunciatory.",
    },
}

# ── Dignity prefixes ───────────────────────────────────────────────────────────
_DIGNITY_PREFIX = {
    "exalted":      "Strongly dignified (exalted) -- ",
    "exalted_exact":"At peak exaltation -- ",
    "moolatrikona": "In Moolatrikona (high dignity) -- ",
    "own_sign":     "In own sign -- ",
    "friendly":     "In friendly sign -- ",
    "neutral":      "",
    "enemy":        "In enemy sign (challenged) -- results delayed or obstructed; ",
    "debilitated":  "Debilitated (neecha) -- significations compromised; ",
}

# ── Dasha life-area tendencies ────────────────────────────────────────────────
_DASHA_THEMES = {
    "Sun":     ("authority, government service, leadership, vitality and father's matters",
                "ego clashes, government setbacks, career obstacles and health of heart/eyes"),
    "Moon":    ("emotions, mother, property, mental peace, public dealings and travel",
                "emotional instability, mother's health, anxiety, property disputes and fluctuating finances"),
    "Mars":    ("courage, energy, real estate, siblings and competitive victories",
                "accidents, injuries, conflicts, property disputes and anger management challenges"),
    "Mercury": ("business, communication, education, trade and analytical career advances",
                "indecision, nervous disorders, communication misunderstandings and skin issues"),
    "Jupiter": ("wisdom, children, higher education, religion, wealth expansion and fortune",
                "overexpansion leading to loss, liver issues, legal troubles and false optimism"),
    "Venus":   ("love, marriage, arts, luxury, vehicles, pleasures and comforts",
                "relationship problems, health through excess, financial losses on luxury"),
    "Saturn":  ("career discipline, longevity, karma yoga, steady wealth and respect from elders",
                "depression, chronic illness, career stagnation, isolation and delays in all areas"),
    "Rahu":    ("ambition, unconventional methods, technology, foreign connections and sudden gains",
                "confusion, deceit, sudden falls, foreign problems and obsession leading to downfall"),
    "Ketu":    ("spirituality, detachment, past-life wisdom, moksha practices and occult mastery",
                "aimlessness, health crises, sudden losses and separations from loved ones"),
}


def _house_lord(lagna_sign: str, house_num: int) -> str:
    """Return the natural lord of house_num given whole-sign lagna."""
    lagna_idx = _SIGN_IDX.get(lagna_sign, 0)
    sign = _SIGNS[(lagna_idx + house_num - 1) % 12]
    return _SIGN_LORDS[sign]


def _planet_sentence(pname: str, house: int, dignity: str, retrograde: bool = False) -> str:
    """Build one interpretation sentence for a planet in a house."""
    base = PLANET_IN_HOUSE.get(pname, {}).get(house, "")
    if not base:
        return ""
    prefix = _DIGNITY_PREFIX.get(dignity, "")
    retro_note = " [Retrograde: energy turns inward; results may come after delay or in non-linear ways.]" if retrograde else ""
    return f"{prefix}{base}{retro_note}"


def _karaka_area_sentence(planet: str, house: int, dignity: str, retrograde: bool, area: str) -> str:
    """
    Generate a life-area-contextual interpretation for a natural karaka planet.
    Frames the planet's house placement for the specific life domain so the same
    planet (e.g. Jupiter in H10) doesn't output career text inside the Children or
    Spirituality sections.
    """
    retro = " [Retrograde: energy turns inward; timing may shift or be non-linear.]" if retrograde else ""
    strong = dignity in {"exalted", "own_sign", "moolatrikona", "friendly"}
    dig_label = {
        "exalted": "exalted", "own_sign": "in own sign",
        "moolatrikona": "in Moolatrikona", "friendly": "in a friendly sign",
        "neutral": "in a neutral sign", "enemy": "in an enemy sign",
        "debilitated": "debilitated",
    }.get(dignity, "placed")

    _AREA_KARAKA: dict[tuple, tuple] = {
        ("children", "Jupiter"): (
            f"Jupiter ({dig_label}) in H{house}: children are blessed with intelligence, moral strength, and ambition; the native's dharmic life creates an auspicious environment for progeny.{retro}",
            f"Jupiter ({dig_label}) in H{house}: children karma has some complexity -- timing of progeny may be delayed or parenthood requires extra effort; once arrived, children bring genuine wisdom.{retro}",
        ),
        ("children", "Saturn"): (
            f"Saturn ({dig_label}) in H{house}: children arrive later in life but prove stable and accomplished; they inherit the native's disciplined work ethic and perseverance.{retro}",
            f"Saturn ({dig_label}) in H{house}: delays or limitations around children are possible; first child may come after challenges; children tend toward seriousness and responsibility.{retro}",
        ),
        ("home", "Moon"): (
            f"Moon ({dig_label}) in H{house}: emotional life is rich and the mother is a central nurturing force; home provides genuine comfort, peace, and emotional security to the native.{retro}",
            f"Moon ({dig_label}) in H{house}: emotional fluctuations colour domestic life; mother's health or presence may be a sensitive area; home is both a refuge and a place of inner work.{retro}",
        ),
        ("siblings", "Mars"): (
            f"Mars ({dig_label}) in H{house}: siblings are strong, courageous, and generally supportive; the native and siblings share competitive drive and mutual encouragement throughout life.{retro}",
            f"Mars ({dig_label}) in H{house}: sibling relationships have competitive or friction-prone edges; the native's own courage is strong, but disputes with siblings require careful handling.{retro}",
        ),
        ("father", "Jupiter"): (
            f"Jupiter ({dig_label}) in H{house}: the father, guru, or mentor is wise and accomplished; their influence shapes the native's dharma, fortune, and approach to higher knowledge.{retro}",
            f"Jupiter ({dig_label}) in H{house}: the father or guru principle brings karmic complexity; wisdom is earned through challenge rather than inherited; higher guidance must be sought actively.{retro}",
        ),
        ("father", "Sun"): (
            f"Sun ({dig_label}) in H{house}: father is a strong, authoritative, and influential figure whose example directly shapes the native's ambition and leadership style.{retro}",
            f"Sun ({dig_label}) in H{house}: father's presence or authority may be limited or complex; the native builds personal authority independently, without relying on paternal support.{retro}",
        ),
        ("love", "Venus"): (
            f"Venus ({dig_label}) in H{house}: romantic life is genuine and pleasurable; the native naturally attracts loving, aesthetic, or culturally refined partners; love deepens into lasting bonds.{retro}",
            f"Venus ({dig_label}) in H{house}: romantic relationships are coloured by differing values or expectations around beauty and material life; love tests personal values before it deepens.{retro}",
        ),
        ("love", "Jupiter"): (
            f"Jupiter ({dig_label}) in H{house}: marriage brings wisdom and dharmic expansion; the spouse is educated, virtuous, and a genuine life guide who elevates the native's perspective.{retro}",
            f"Jupiter ({dig_label}) in H{house}: marriage may come after karmic testing; once established, the partnership grows through shared dharma, learning, and philosophical alignment.{retro}",
        ),
        ("love", "Mars"): (
            f"Mars ({dig_label}) in H{house}: passion and desire are strong; the native pursues romance with energy and directness; physical attraction and initiative characterise love life.{retro}",
            f"Mars ({dig_label}) in H{house}: passion is intense but can turn to friction; Manglik energy in love calls for patience and choosing a partner with compatible drive and temperament.{retro}",
        ),
        ("love", "Moon"): (
            f"Moon ({dig_label}) in H{house}: emotional bonding and nurturing define the native's approach to love; they seek security, emotional depth, and family connection in partnership.{retro}",
            f"Moon ({dig_label}) in H{house}: emotional fluctuations influence romantic choices; the native may be over-sensitive in relationships; consistent emotional grounding is essential.{retro}",
        ),
        ("finance", "Jupiter"): (
            f"Jupiter ({dig_label}) in H{house}: wealth expands through wisdom, dharmic living, and auspicious timing; Jupiter's placement creates Dhana Yoga potential across financial houses.{retro}",
            f"Jupiter ({dig_label}) in H{house}: wealth requires dharmic effort; overconfidence or excessive generosity should be balanced with practical financial discipline and long-term planning.{retro}",
        ),
        ("finance", "Venus"): (
            f"Venus ({dig_label}) in H{house}: financial prosperity through aesthetic, creative, or pleasure-linked ventures; the native genuinely attracts material comfort and financial ease.{retro}",
            f"Venus ({dig_label}) in H{house}: expenses on luxury or pleasure may outpace income; financial discipline around lifestyle choices and indulgences is important for stability.{retro}",
        ),
        ("spirituality", "Ketu"): (
            f"Ketu ({dig_label}) in H{house}: deep spiritual inclination carried from past-life wisdom; liberation (moksha) is a genuine life theme; detachment from material outcomes supports inner growth.{retro}",
            f"Ketu ({dig_label}) in H{house}: spiritual path has karmic complexity; the native oscillates between worldly engagement and renunciation before finding their authentic dharmic centre.{retro}",
        ),
        ("spirituality", "Jupiter"): (
            f"Jupiter ({dig_label}) in H{house}: consciousness expands through wisdom and dharmic service; the native finds spiritual fulfilment through teaching, healing, or generous service to society.{retro}",
            f"Jupiter ({dig_label}) in H{house}: spiritual growth comes through karmic challenge; over-attachment to belief systems or excessive optimism may delay genuine inner awakening.{retro}",
        ),
        ("education", "Mercury"): (
            f"Mercury ({dig_label}) in H{house}: sharp intellect and genuine aptitude for learning; excels in analytical, communicative, or technical subjects; multiple educational streams are possible.{retro}",
            f"Mercury ({dig_label}) in H{house}: academic learning benefits from structured effort and focus; analytical abilities are present but need consistent practice to fully develop.{retro}",
        ),
        ("education", "Jupiter"): (
            f"Jupiter ({dig_label}) in H{house}: higher education and wisdom accumulation are strongly favoured; philosophical, legal, spiritual, or financial disciplines are areas of natural excellence.{retro}",
            f"Jupiter ({dig_label}) in H{house}: higher learning requires sustained effort; breadth of curiosity may initially outpace depth; eventual mastery comes through patience and focused study.{retro}",
        ),
        ("health", "Saturn"): (
            f"Saturn ({dig_label}) in H{house}: health is maintained through disciplined routine and preventive care; longevity is supported when karmic duty is fulfilled consistently.{retro}",
            f"Saturn ({dig_label}) in H{house}: chronic or recurring health challenges around bones, joints, or the nervous system; preventive care and dietary discipline are essential throughout life.{retro}",
        ),
        ("health", "Mars"): (
            f"Mars ({dig_label}) in H{house}: physical vitality and recovery power are strong; immunity is robust; the native thrives with regular exercise and an active lifestyle.{retro}",
            f"Mars ({dig_label}) in H{house}: susceptibility to inflammation, accidents, or surgical events; caution in physically risky situations; managing anger and stress directly improves health outcomes.{retro}",
        ),
        ("health", "Moon"): (
            f"Moon ({dig_label}) in H{house}: emotional balance strongly supports physical health; the mind-body connection is powerful; mental peace directly contributes to longevity.{retro}",
            f"Moon ({dig_label}) in H{house}: emotional fluctuations and digestive sensitivity may affect overall health; adequate rest, emotional support, and stress reduction are key wellbeing pillars.{retro}",
        ),
    }

    key = (area, planet)
    if key in _AREA_KARAKA:
        pos_text, neg_text = _AREA_KARAKA[key]
        return pos_text if strong else neg_text

    return _planet_sentence(planet, house, dignity, retrograde)


def _lord_sentence(house_num: int, lord_house: int, dignity: str) -> str:
    """Return lord-in-house reading."""
    base = LORD_IN_HOUSE.get(house_num, {}).get(lord_house, "")
    if not base:
        return ""
    prefix = _DIGNITY_PREFIX.get(dignity, "")
    return f"H{house_num} lord in H{lord_house} -- {prefix}{base}"


def _sign_element(sign: str) -> str:
    fire  = ["Aries","Leo","Sagittarius"]
    earth = ["Taurus","Virgo","Capricorn"]
    air   = ["Gemini","Libra","Aquarius"]
    water = ["Cancer","Scorpio","Pisces"]
    if sign in fire:  return "fire"
    if sign in earth: return "earth"
    if sign in air:   return "air"
    if sign in water: return "water"
    return ""


def _sign_quality(sign: str) -> str:
    movable = ["Aries","Cancer","Libra","Capricorn"]
    fixed   = ["Taurus","Leo","Scorpio","Aquarius"]
    dual    = ["Gemini","Virgo","Sagittarius","Pisces"]
    if sign in movable: return "movable (changeable)"
    if sign in fixed:   return "fixed (stable)"
    if sign in dual:    return "dual (flexible)"
    return ""


# ═══════════════════════════════════════════════════════════════════════════════
#  LIFE AREA READERS
# ═══════════════════════════════════════════════════════════════════════════════

def _read_personality(planets: dict, lagna: dict, all_houses: dict) -> str:
    lagna_sign = lagna.get("sign", "")
    lagna_lord = lagna.get("lord", "")
    ll = planets.get(lagna_lord, {})
    ll_h = ll.get("house", 0)
    ll_dg = ll.get("dignity", "neutral")
    ll_sign = ll.get("sign", "")

    sun = planets.get("Sun", {})
    moon = planets.get("Moon", {})
    asc_element = _sign_element(lagna_sign)
    asc_quality = _sign_quality(lagna_sign)

    parts = []
    parts.append(f"PERSONALITY & PHYSICAL CONSTITUTION")
    parts.append(f"Your Lagna (Ascendant) is {lagna_sign}, a {asc_element}-element, {asc_quality} sign. "
                 f"This shapes your outward personality, physical body, and life direction. "
                 f"{lagna_sign} rising people are known for "
                 + _lagna_personality(lagna_sign) + ".")

    parts.append(f"Lagna lord {lagna_lord} is placed in the {_ordinal(ll_h)} house in {ll_sign} "
                 f"({ll_dg} dignity). " + _lord_sentence(1, ll_h, ll_dg))

    if sun:
        s = _planet_sentence("Sun", sun.get("house", 0), sun.get("dignity", "neutral"), sun.get("retrograde", False))
        if s:
            parts.append(f"Sun (soul and vitality) in H{sun.get('house',0)}: {s}")

    if moon:
        m = _planet_sentence("Moon", moon.get("house", 0), moon.get("dignity", "neutral"), moon.get("retrograde", False))
        if m:
            parts.append(f"Moon (mind and emotions) in H{moon.get('house',0)}: {m}")

    # H1 occupants
    h1 = all_houses.get("H1", {})
    occ = [p for p in h1.get("occupants", []) if p not in ("Sun",)]
    for p in occ[:2]:
        pd = planets.get(p, {})
        s = _planet_sentence(p, 1, pd.get("dignity", "neutral"), pd.get("retrograde", False))
        if s:
            parts.append(f"{p} in the Lagna: {s}")

    parts.append(f"Overall constitution: H1 is {all_houses.get('H1',{}).get('strength','moderate')} in strength. "
                 + _constitution_note(all_houses.get("H1", {}), ll_dg))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _lagna_personality(sign: str) -> str:
    traits = {
        "Aries":       "initiative, boldness, and competitive drive; the pioneer who acts first and thinks later; physically energetic and quick-tempered",
        "Taurus":      "patience, determination, sensuality, and love of material comforts; stubborn but reliable; strong aesthetic sense",
        "Gemini":      "curiosity, wit, adaptability, and love of communication; the natural networker and storyteller; duality in nature",
        "Cancer":      "emotional depth, nurturing instincts, strong family ties, and intuitive nature; deeply connected to home and mother",
        "Leo":         "natural leadership, pride, creativity, and desire for recognition; the natural performer and king who commands attention",
        "Virgo":       "analytical precision, service orientation, health-consciousness, and perfectionism; practical problem-solver",
        "Libra":       "social grace, fairness, love of beauty, and strong partnership orientation; the diplomat who seeks balance in all things",
        "Scorpio":     "intensity, penetrating insight, secretiveness, and transformative power; magnetic personality with deep emotional reserves",
        "Sagittarius": "philosophical mind, love of freedom, optimism, and adventurous spirit; the seeker of higher truth and distant horizons",
        "Capricorn":   "discipline, ambition, practicality, and patience; the steady climber who builds lasting structures through consistent effort",
        "Aquarius":    "intellectual independence, humanitarianism, unconventionality, and social consciousness; the innovator and visionary",
        "Pisces":      "compassion, imagination, spiritual sensitivity, and fluid nature; the mystic and artist who absorbs the feelings of others",
    }
    return traits.get(sign, "unique qualities specific to their sign")


def _constitution_note(h1: dict, ll_dg: str) -> str:
    strength = h1.get("strength", "moderate")
    if strength == "strong":
        return "Physical constitution is robust; energy levels are generally good throughout life."
    if strength == "weak":
        return "Physical constitution requires care; attention to health and lifestyle is advised."
    return "Physical constitution is moderate; with good habits, good health is maintained."


def _read_education(planets: dict, lagna: dict, all_houses: dict) -> str:
    lagna_sign = lagna.get("sign", "")
    parts = ["EDUCATION (EARLY & HIGHER)"]

    # H4 for early education
    h4 = all_houses.get("H4", {})
    h4_lord = h4.get("lord", "")
    h4_lh = h4.get("lord_house", 0)
    h4_dg = h4.get("lord_dignity", "neutral")
    mercury = planets.get("Mercury", {})
    jupiter = planets.get("Jupiter", {})

    parts.append(f"Early Education (H4 -- Vidya Bhava): H4 sign is {h4.get('sign','')}; "
                 f"lord {h4_lord} is in H{h4_lh} ({h4_dg}). " + _lord_sentence(4, h4_lh, h4_dg))

    seen: set = set()
    if h4.get("occupants"):
        for p in h4.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 4, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} occupying H4: {s}")

    if "Mercury" not in seen:
        parts.append(f"Mercury (karaka of education and intellect) is in H{mercury.get('house',0)} "
                     f"in {mercury.get('sign','')} ({mercury.get('dignity','neutral')} dignity). "
                     + _karaka_area_sentence("Mercury", mercury.get("house", 0), mercury.get("dignity", "neutral"), mercury.get("retrograde", False), "education"))
    seen.add("Mercury")

    # H5 for higher education and intelligence
    h5 = all_houses.get("H5", {})
    h5_lord = h5.get("lord", "")
    h5_lh = h5.get("lord_house", 0)
    h5_dg = h5.get("lord_dignity", "neutral")
    parts.append(f"Higher Education & Intelligence (H5 -- Putra Bhava): lord {h5_lord} is in H{h5_lh} ({h5_dg}). "
                 + _lord_sentence(5, h5_lh, h5_dg))

    # Jupiter for higher wisdom
    if jupiter and "Jupiter" not in seen:
        parts.append(f"Jupiter (higher wisdom and dharma) in H{jupiter.get('house',0)}: "
                     + _karaka_area_sentence("Jupiter", jupiter.get("house", 0), jupiter.get("dignity", "neutral"), jupiter.get("retrograde", False), "education"))

    # H9 for philosophy and higher learning
    h9 = all_houses.get("H9", {})
    h9_lord = h9.get("lord", "")
    h9_lh = h9.get("lord_house", 0)
    h9_dg = h9.get("lord_dignity", "neutral")
    parts.append(f"Philosophy & Higher Learning (H9 -- Dharma Bhava): lord {h9_lord} in H{h9_lh} ({h9_dg}). "
                 + _lord_sentence(9, h9_lh, h9_dg))

    ed_strength = h5.get("strength", "moderate")
    parts.append(f"Education summary: H5 is {ed_strength}. "
                 + ("Academic and creative intelligence are well-developed; success in studies is indicated." if ed_strength == "strong"
                    else "Academic efforts require discipline; with persistence, educational goals are achieved." if ed_strength == "weak"
                    else "Average academic potential; specific subjects aligned with planetary strengths will excel."))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_career(planets: dict, lagna: dict, all_houses: dict, dasha: dict) -> str:
    parts = ["CAREER, STATUS & AUTHORITY"]

    h10 = all_houses.get("H10", {})
    h10_lord = h10.get("lord", "")
    h10_lh = h10.get("lord_house", 0)
    h10_dg = h10.get("lord_dignity", "neutral")
    saturn = planets.get("Saturn", {})
    sun = planets.get("Sun", {})
    maha = dasha.get("mahadasha", {}) or {}

    parts.append(f"10th House (Karma Bhava -- Career): sign is {h10.get('sign','')}; "
                 f"lord {h10_lord} is in H{h10_lh} ({h10_dg} dignity). "
                 + _lord_sentence(10, h10_lh, h10_dg))

    if h10.get("occupants"):
        for p in h10.get("occupants", [])[:2]:
            pd = planets.get(p, {})
            s = _planet_sentence(p, 10, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in the Career house: {s}")

    parts.append(f"Saturn (karaka of career and karma) in H{saturn.get('house',0)}, "
                 f"{saturn.get('sign','')} ({saturn.get('dignity','neutral')}): "
                 + _planet_sentence("Saturn", saturn.get("house", 0), saturn.get("dignity", "neutral"), saturn.get("retrograde", False)))

    parts.append(f"Sun (authority and status) in H{sun.get('house',0)}, "
                 f"{sun.get('sign','')} ({sun.get('dignity','neutral')}): "
                 + _planet_sentence("Sun", sun.get("house", 0), sun.get("dignity", "neutral"), sun.get("retrograde", False)))

    # D10 hint — career timing in terms of current Mahadasha
    _mp = maha.get("planet", "")
    _mp_until = str(maha.get("end_date", ""))[:7]
    _mp_dig = planets.get(_mp, {}).get("dignity", "neutral")
    if _mp:
        if _mp_dig in ("exalted", "own_sign", "moolatrikona", "friendly"):
            _timing = (f"The current {_mp} Mahadasha (until {_mp_until}) is favourable for career: "
                       + _DASHA_THEMES.get(_mp, ("growth and opportunity", ""))[0] + ".")
        else:
            _raw = _DASHA_THEMES.get(_mp, ("", "patience and perseverance"))[1]
            _first_theme = _raw.split(",")[0].strip().lower() if _raw else "patience"
            _timing = (f"The current {_mp} Mahadasha (until {_mp_until}) is a karmic period in career; "
                       f"it calls for discipline and realistic expectations around {_first_theme} "
                       f"before eventual stabilisation and recognition.")
        parts.append(f"Career timing: {_timing}")

    h10_strength = h10.get("strength", "moderate")
    parts.append("Career outlook: "
                 + ("Strong career indicators; authority and recognition are attainable; government or corporate leadership potential." if h10_strength == "strong"
                    else "Career requires sustained effort; obstacles present but eventual success through discipline." if h10_strength == "weak"
                    else "Moderate career potential; consistent effort brings steady professional growth."))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_finance(planets: dict, lagna: dict, all_houses: dict, yogas: list) -> str:
    parts = ["WEALTH & FINANCE"]

    h2 = all_houses.get("H2", {})
    h11 = all_houses.get("H11", {})
    h5 = all_houses.get("H5", {})
    jupiter = planets.get("Jupiter", {})
    venus = planets.get("Venus", {})

    parts.append(f"2nd House (Dhana Bhava -- Wealth): sign {h2.get('sign','')}; "
                 f"lord {h2.get('lord','')} in H{h2.get('lord_house',0)} ({h2.get('lord_dignity','neutral')}). "
                 + _lord_sentence(2, h2.get("lord_house", 0), h2.get("lord_dignity", "neutral")))

    parts.append(f"11th House (Labha Bhava -- Income & Gains): sign {h11.get('sign','')}; "
                 f"lord {h11.get('lord','')} in H{h11.get('lord_house',0)} ({h11.get('lord_dignity','neutral')}). "
                 + _lord_sentence(11, h11.get("lord_house", 0), h11.get("lord_dignity", "neutral")))

    seen: set = set()
    if h2.get("occupants"):
        for p in h2.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 2, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in the Wealth house: {s}")

    if "Jupiter" not in seen:
        parts.append(f"Jupiter (wealth karaka) in H{jupiter.get('house',0)}, {jupiter.get('sign','')} "
                     f"({jupiter.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Jupiter", jupiter.get("house", 0), jupiter.get("dignity", "neutral"), jupiter.get("retrograde", False), "finance"))
    seen.add("Jupiter")

    if "Venus" not in seen:
        parts.append(f"Venus (material prosperity) in H{venus.get('house',0)}, {venus.get('sign','')} "
                     f"({venus.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Venus", venus.get("house", 0), venus.get("dignity", "neutral"), venus.get("retrograde", False), "finance"))

    # 5th house speculation
    parts.append(f"5th House (Speculation & Investments): lord {h5.get('lord','')} in H{h5.get('lord_house',0)} "
                 f"({h5.get('lord_dignity','neutral')}). " + _lord_sentence(5, h5.get("lord_house", 0), h5.get("lord_dignity", "neutral")))

    # Dhana Yoga
    dhana_yogas = [y for y in yogas if "Dhana" in y.get("name", "") or "wealth" in y.get("effect", "").lower()]
    if dhana_yogas:
        parts.append("Wealth Yogas detected: " + "; ".join(y["name"] for y in dhana_yogas) + ". " +
                     dhana_yogas[0].get("effect", ""))

    wealth_strength = h2.get("strength", "moderate")
    income_strength = h11.get("strength", "moderate")
    parts.append("Financial summary: "
                 + (f"Both wealth (H2 {wealth_strength}) and income (H11 {income_strength}) houses are well-positioned; "
                    "financial accumulation and income flow are both supported."
                    if wealth_strength == "strong" and income_strength == "strong"
                    else "Financial areas have mixed strength; disciplined saving and cautious investment are advised."
                    if wealth_strength == "weak" or income_strength == "weak"
                    else "Moderate financial potential; steady, consistent accumulation is the key pattern."))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_love_marriage(planets: dict, lagna: dict, all_houses: dict, yogas: list) -> str:
    parts = ["LOVE LIFE, ROMANCE & MARRIAGE"]

    h5 = all_houses.get("H5", {})
    h7 = all_houses.get("H7", {})
    venus = planets.get("Venus", {})
    mars = planets.get("Mars", {})
    jupiter = planets.get("Jupiter", {})
    moon = planets.get("Moon", {})

    parts.append(f"5th House (Romance & Love): sign {h5.get('sign','')}; "
                 f"lord {h5.get('lord','')} in H{h5.get('lord_house',0)} ({h5.get('lord_dignity','neutral')}). "
                 + _lord_sentence(5, h5.get("lord_house", 0), h5.get("lord_dignity", "neutral")))

    parts.append(f"7th House (Marriage & Partnerships): sign {h7.get('sign','')}; "
                 f"lord {h7.get('lord','')} in H{h7.get('lord_house',0)} ({h7.get('lord_dignity','neutral')}). "
                 + _lord_sentence(7, h7.get("lord_house", 0), h7.get("lord_dignity", "neutral")))

    seen: set = set()
    if h7.get("occupants"):
        for p in h7.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 7, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in the Marriage house: {s}")

    if "Venus" not in seen:
        parts.append(f"Venus (love, beauty, and marriage karaka) in H{venus.get('house',0)}, "
                     f"{venus.get('sign','')} ({venus.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Venus", venus.get("house", 0), venus.get("dignity", "neutral"), venus.get("retrograde", False), "love"))
    seen.add("Venus")

    if "Mars" not in seen:
        parts.append(f"Mars (passion, desire) in H{mars.get('house',0)}: "
                     + _karaka_area_sentence("Mars", mars.get("house", 0), mars.get("dignity", "neutral"), mars.get("retrograde", False), "love"))
    seen.add("Mars")

    if "Moon" not in seen:
        parts.append(f"Moon (emotional bonding) in H{moon.get('house',0)}: "
                     + _karaka_area_sentence("Moon", moon.get("house", 0), moon.get("dignity", "neutral"), moon.get("retrograde", False), "love"))

    # Marriage timing indicators
    h7_lord_h = h7.get("lord_house", 0)
    h7_dg = h7.get("lord_dignity", "neutral")
    if h7_lord_h in (1, 5, 11):
        parts.append("Marriage timing indicators: 7th lord in angular/trine position suggests early to mid-life marriage in the dasha of Venus or 7th lord.")
    elif h7_lord_h in (6, 8, 12):
        parts.append("Marriage timing indicators: 7th lord in a difficult house suggests delayed or challenging marriage; counselling and patience are advised.")
    else:
        parts.append("Marriage timing indicators: 7th lord in a moderate position; marriage in Venus or 7th lord dasha/antardasha at the appropriate life stage.")

    # Manglik
    manglik = any("Manglik" in y.get("name", "") for y in yogas)
    if manglik:
        parts.append("Note: Manglik Dosha is present (Mars in H1/2/4/7/8/12). Marriage to a fellow Manglik is traditionally advised; otherwise perform appropriate remedies before marriage.")

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_children(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["CHILDREN & PROGENY"]

    h5 = all_houses.get("H5", {})
    jupiter = planets.get("Jupiter", {})

    parts.append(f"5th House (Putra Bhava -- Children & Intelligence): sign {h5.get('sign','')}; "
                 f"lord {h5.get('lord','')} in H{h5.get('lord_house',0)} ({h5.get('lord_dignity','neutral')} dignity). "
                 + _lord_sentence(5, h5.get("lord_house", 0), h5.get("lord_dignity", "neutral")))

    seen: set = set()
    if h5.get("occupants"):
        for p in h5.get("occupants", [])[:3]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 5, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in H5: {s}")

    if "Jupiter" not in seen:
        parts.append(f"Jupiter (karaka of children and progeny) in H{jupiter.get('house',0)}, "
                     f"{jupiter.get('sign','')} ({jupiter.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Jupiter", jupiter.get("house", 0), jupiter.get("dignity", "neutral"), jupiter.get("retrograde", False), "children"))

    h5_strength = h5.get("strength", "moderate")
    sat_in_h5 = "Saturn" in h5.get("occupants", [])
    rahu_in_h5 = "Rahu" in h5.get("occupants", [])

    if h5_strength == "strong" and not sat_in_h5:
        parts.append("Children forecast: Strong 5th house indicates happiness through children; children are likely to be intelligent, successful, and supportive.")
    elif sat_in_h5:
        parts.append("Children forecast: Saturn in H5 indicates delayed children or fewer children; after initial challenges, children bring long-term stability.")
    elif rahu_in_h5:
        parts.append("Children forecast: Rahu in H5 indicates unconventional children or unique circumstances around progeny; karmic past-life connections with children.")
    elif h5_strength == "weak":
        parts.append("Children forecast: Challenges in progeny matters; medical consultation and appropriate remedies (Jupiter worship, feeding cows) may help.")
    else:
        parts.append("Children forecast: Moderate 5th house; normal family life with children; timing aligns with Jupiter Mahadasha or antardasha.")

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_health(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["HEALTH & LONGEVITY"]

    h1 = all_houses.get("H1", {})
    h6 = all_houses.get("H6", {})
    h8 = all_houses.get("H8", {})
    saturn = planets.get("Saturn", {})
    mars = planets.get("Mars", {})
    moon = planets.get("Moon", {})
    lagna_sign = lagna.get("sign", "")

    parts.append(f"General Health (H1 -- Physical Constitution): {h1.get('strength','moderate')} strength. "
                 + _constitution_note(h1, h1.get("lord_dignity", "neutral")))

    parts.append(f"6th House (Health, Disease & Service): sign {h6.get('sign','')}; "
                 f"lord {h6.get('lord','')} in H{h6.get('lord_house',0)} ({h6.get('lord_dignity','neutral')}). "
                 + _lord_sentence(6, h6.get("lord_house", 0), h6.get("lord_dignity", "neutral")))

    if h6.get("occupants"):
        for p in h6.get("occupants", [])[:2]:
            pd = planets.get(p, {})
            s = _planet_sentence(p, 6, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in H6 (health house): {s}")

    parts.append(f"8th House (Longevity & Transformation): {h8.get('strength','moderate')} strength; "
                 f"lord {h8.get('lord','')} in H{h8.get('lord_house',0)} ({h8.get('lord_dignity','neutral')}). "
                 + _lord_sentence(8, h8.get("lord_house", 0), h8.get("lord_dignity", "neutral")))

    parts.append(f"Saturn (longevity and karmic health) in H{saturn.get('house',0)}, "
                 f"{saturn.get('sign','')} ({saturn.get('dignity','neutral')}): "
                 + _planet_sentence("Saturn", saturn.get("house", 0), saturn.get("dignity", "neutral"), saturn.get("retrograde", False)))

    # Body part ruled by Lagna sign
    body_parts = {
        "Aries":"head and brain", "Taurus":"neck, throat and vocal cords", "Gemini":"shoulders, arms and lungs",
        "Cancer":"chest, breasts and stomach", "Leo":"heart, spine and upper back", "Virgo":"intestines and digestive system",
        "Libra":"kidneys, lower back and skin", "Scorpio":"reproductive organs and pelvis", "Sagittarius":"hips, thighs and liver",
        "Capricorn":"knees, bones and joints", "Aquarius":"ankles and circulatory system", "Pisces":"feet and lymphatic system",
    }
    parts.append(f"Body focus for {lagna_sign} Lagna: particular attention advised to "
                 + body_parts.get(lagna_sign, "general health") + ". Preventive care in these areas recommended.")

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_home_family(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["HOME, MOTHER & FAMILY ENVIRONMENT"]

    h4 = all_houses.get("H4", {})
    h2 = all_houses.get("H2", {})
    moon = planets.get("Moon", {})

    parts.append(f"4th House (Sukha Bhava -- Home & Mother): sign {h4.get('sign','')}; "
                 f"lord {h4.get('lord','')} in H{h4.get('lord_house',0)} ({h4.get('lord_dignity','neutral')} dignity). "
                 + _lord_sentence(4, h4.get("lord_house", 0), h4.get("lord_dignity", "neutral")))

    seen: set = set()
    if h4.get("occupants"):
        for p in h4.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 4, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in H4: {s}")

    if "Moon" not in seen:
        parts.append(f"Moon (mother, emotions and domestic peace) in H{moon.get('house',0)}, "
                     f"{moon.get('sign','')} ({moon.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Moon", moon.get("house", 0), moon.get("dignity", "neutral"), moon.get("retrograde", False), "home"))

    parts.append(f"2nd House (Family and Speech): lord {h2.get('lord','')} in H{h2.get('lord_house',0)} "
                 f"({h2.get('lord_dignity','neutral')}). " + _lord_sentence(2, h2.get("lord_house", 0), h2.get("lord_dignity", "neutral")))

    h4_strength = h4.get("strength", "moderate")
    parts.append("Home and family summary: "
                 + ("Excellent domestic life indicated; happy home, supportive mother, good property prospects." if h4_strength == "strong"
                    else "Domestic challenges possible; relationship with mother may need nurturing; home environment improves with patience." if h4_strength == "weak"
                    else "Moderate domestic situation; home life is generally stable with occasional disruptions."))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_siblings(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["SIBLINGS & COURAGE"]

    h3 = all_houses.get("H3", {})
    h11 = all_houses.get("H11", {})
    mars = planets.get("Mars", {})

    parts.append(f"3rd House (Parakrama Bhava -- Siblings & Courage): sign {h3.get('sign','')}; "
                 f"lord {h3.get('lord','')} in H{h3.get('lord_house',0)} ({h3.get('lord_dignity','neutral')}). "
                 + _lord_sentence(3, h3.get("lord_house", 0), h3.get("lord_dignity", "neutral")))

    seen: set = set()
    if h3.get("occupants"):
        for p in h3.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 3, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in H3: {s}")

    if "Mars" not in seen:
        parts.append(f"Mars (karaka of siblings and courage) in H{mars.get('house',0)}, "
                     f"{mars.get('sign','')} ({mars.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Mars", mars.get("house", 0), mars.get("dignity", "neutral"), mars.get("retrograde", False), "siblings"))

    parts.append(f"11th House (elder siblings) lord {h11.get('lord','')} in H{h11.get('lord_house',0)}: "
                 + _lord_sentence(11, h11.get("lord_house", 0), h11.get("lord_dignity", "neutral")))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_father_fortune(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["FATHER, FORTUNE & HIGHER GUIDANCE"]

    h9 = all_houses.get("H9", {})
    jupiter = planets.get("Jupiter", {})
    sun = planets.get("Sun", {})

    parts.append(f"9th House (Dharma Bhava -- Fortune & Father): sign {h9.get('sign','')}; "
                 f"lord {h9.get('lord','')} in H{h9.get('lord_house',0)} ({h9.get('lord_dignity','neutral')} dignity). "
                 + _lord_sentence(9, h9.get("lord_house", 0), h9.get("lord_dignity", "neutral")))

    seen: set = set()
    if h9.get("occupants"):
        for p in h9.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 9, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in H9: {s}")

    if "Jupiter" not in seen:
        parts.append(f"Jupiter (dharma, guru, and higher knowledge) in H{jupiter.get('house',0)}, "
                     f"{jupiter.get('sign','')} ({jupiter.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Jupiter", jupiter.get("house", 0), jupiter.get("dignity", "neutral"), jupiter.get("retrograde", False), "father"))
    seen.add("Jupiter")

    if "Sun" not in seen:
        parts.append(f"Sun (father and authority) in H{sun.get('house',0)}: "
                     + _karaka_area_sentence("Sun", sun.get("house", 0), sun.get("dignity", "neutral"), sun.get("retrograde", False), "father"))

    h9_strength = h9.get("strength", "moderate")
    parts.append("Fortune summary: "
                 + ("Very fortunate chart; luck, divine grace, and father's blessings are strong; overseas connections and higher education are strongly supported." if h9_strength == "strong"
                    else "Fortune requires active effort; dharmic living and consistent good deeds build luck over time." if h9_strength == "weak"
                    else "Moderate fortune; steady dharmic effort brings gradual improvement in luck and divine support."))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_spirituality(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["SPIRITUALITY, MOKSHA & FOREIGN CONNECTIONS"]

    h12 = all_houses.get("H12", {})
    h9 = all_houses.get("H9", {})
    ketu = planets.get("Ketu", {})
    saturn = planets.get("Saturn", {})
    jupiter = planets.get("Jupiter", {})

    parts.append(f"12th House (Vyaya Bhava -- Moksha & Foreign): sign {h12.get('sign','')}; "
                 f"lord {h12.get('lord','')} in H{h12.get('lord_house',0)} ({h12.get('lord_dignity','neutral')}). "
                 + _lord_sentence(12, h12.get("lord_house", 0), h12.get("lord_dignity", "neutral")))

    seen: set = set()
    if h12.get("occupants"):
        for p in h12.get("occupants", [])[:2]:
            seen.add(p)
            pd = planets.get(p, {})
            s = _planet_sentence(p, 12, pd.get("dignity", "neutral"), pd.get("retrograde", False))
            if s:
                parts.append(f"{p} in H12: {s}")

    if "Ketu" not in seen:
        parts.append(f"Ketu (karaka of spirituality and moksha) in H{ketu.get('house',0)}, "
                     f"{ketu.get('sign','')} ({ketu.get('dignity','neutral')}): "
                     + _karaka_area_sentence("Ketu", ketu.get("house", 0), ketu.get("dignity", "neutral"), ketu.get("retrograde", False), "spirituality"))
    seen.add("Ketu")

    if "Jupiter" not in seen:
        parts.append(f"Jupiter (expansion of consciousness) in H{jupiter.get('house',0)}: "
                     + _karaka_area_sentence("Jupiter", jupiter.get("house", 0), jupiter.get("dignity", "neutral"), jupiter.get("retrograde", False), "spirituality"))

    # Moksha yoga detection
    ketu_h = ketu.get("house", 0)
    jup_h = jupiter.get("house", 0)
    if ketu_h == 12:
        parts.append("Special: Ketu in H12 forms a powerful Moksha Yoga -- spiritual liberation and foreign spiritual connections are strongly indicated in this lifetime.")
    if jup_h == 12:
        parts.append("Jupiter in H12 suggests great spiritual wisdom; potential for ashram life, retreats, or philanthropic work in foreign lands.")

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _read_current_period(planets: dict, lagna: dict, dasha: dict) -> str:
    parts = ["CURRENT PERIOD & PREDICTIONS (DASHA ANALYSIS)"]

    maha = dasha.get("mahadasha", {}) or {}
    ant  = dasha.get("antardasha", {}) or {}
    prat = dasha.get("pratyantardasha", {}) or {}

    mp = maha.get("planet", "")
    ap = ant.get("planet", "")
    pp = prat.get("planet", "")

    mp_data = planets.get(mp, {})
    ap_data = planets.get(ap, {})
    mp_dg   = mp_data.get("dignity", "neutral")
    ap_dg   = ap_data.get("dignity", "neutral")
    mp_h    = mp_data.get("house", 0)
    ap_h    = ap_data.get("house", 0)
    positive_dg = {"exalted", "own_sign", "moolatrikona", "friendly"}

    # -- Period headers (concise — no theme text here, theme text appears ONCE below) --
    if mp:
        mp_label = "favourable" if mp_dg in positive_dg else "karmic (requires patience)"
        parts.append(f"Mahadasha: {mp} (until {str(maha.get('end_date',''))[:7]}) -- "
                     f"{mp} is in H{mp_h} ({mp_data.get('sign','')}) with {mp_dg} dignity [{mp_label}].")

    if ap:
        ap_label = "supportive" if ap_dg in positive_dg else "challenging"
        parts.append(f"Antardasha: {ap} (until {str(ant.get('end_date',''))[:10]}) -- "
                     f"{ap} sub-period is {ap_label} within the {mp} Mahadasha.")

    if pp:
        parts.append(f"Pratyantardasha: {pp} (until {str(prat.get('end_date',''))[:10]}) -- "
                     f"fine-tunes the current sub-period energy.")

    # -- Combined synthesised reading (theme text appears ONCE here only) --
    if mp and ap:
        parts.append(f"Synthesised {mp}/{ap} reading:")
        parts.append("  " + _combined_dasha_reading(mp, ap, mp_dg, ap_dg, mp_h, ap_h, planets))

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _combined_dasha_reading(mp: str, ap: str, mp_dg: str, ap_dg: str,
                            mp_h: int, ap_h: int, planets: dict) -> str:
    positive = {"exalted", "own_sign", "moolatrikona", "friendly"}
    mp_pos = mp_dg in positive
    ap_pos = ap_dg in positive
    same_planet = (mp == ap)

    mp_themes = _DASHA_THEMES.get(mp, ("positive themes", "challenging themes"))
    ap_themes = _DASHA_THEMES.get(ap, ("positive themes", "challenging themes"))

    if same_planet:
        # When Mahadasha and Antardasha are the same planet, the themes are identical.
        # Provide a synthesised, practical reading instead of repeating the same text twice.
        planet_sign = planets.get(mp, {}).get("sign", "")
        if mp_pos:
            return (f"{mp}/{mp} (double dasha of the same planet) is a period of concentrated "
                    f"{mp_themes[0]}. With {mp} in H{mp_h} ({planet_sign}, {mp_dg}), "
                    f"the core themes intensify without relief or opposition — this is the most "
                    f"consistent period for {mp_themes[0].split(',')[0]}. "
                    f"Use this window to build lasting foundations in those areas.")
        else:
            first_theme = mp_themes[1].split(",")[0].strip().lower()
            rest_themes = ", ".join(t.strip() for t in mp_themes[1].split(",")[1:3])
            return (f"{mp}/{mp} (double dasha) concentrates karmic lessons — "
                    f"particularly around {first_theme}. "
                    f"With {mp} in H{mp_h} ({planet_sign}, {mp_dg}), there is no relief sub-lord "
                    f"to ease the pressure. Secondary themes include {rest_themes}. "
                    f"This period calls for disciplined routine, spiritual practice, and realistic "
                    f"expectations. The intensity is temporary; character and resilience built now "
                    f"yield rewards in the following Antardasha.")

    if mp_pos and ap_pos:
        return (f"Both dasha lords are well-placed -- this is a highly productive period. "
                f"{mp} Mahadasha activates: {mp_themes[0]}. "
                f"{ap} antardasha amplifies this through: {ap_themes[0]}.")
    elif mp_pos and not ap_pos:
        return (f"{mp} Mahadasha is strong (themes: {mp_themes[0]}), "
                f"but {ap} antardasha introduces friction around {ap_themes[1].split(',')[0].strip().lower()}. "
                f"Patience during the sub-period brings the Mahadasha's rewards back into view.")
    elif not mp_pos and ap_pos:
        return (f"{mp} Mahadasha is a karmic period (themes: {mp_themes[1]}), "
                f"but {ap} antardasha offers genuine relief through {ap_themes[0].split(',')[0].strip().lower()}. "
                f"Lean into the sub-period's strength to navigate the broader Mahadasha's demands.")
    else:
        first_mp = mp_themes[1].split(",")[0].strip()
        first_ap = ap_themes[1].split(",")[0].strip()
        return (f"Both dasha lords face karmic challenge. The {mp} Mahadasha centres on {first_mp.lower()}; "
                f"the {ap} antardasha adds pressure around {first_ap.lower()}. "
                f"Significant patience, daily spiritual practice, and realistic life expectations are "
                f"required. The native's character deepens substantially through this period of karmic "
                f"purification, and the following Antardasha brings measurable relief.")


def _read_longevity(planets: dict, lagna: dict, all_houses: dict) -> str:
    parts = ["LONGEVITY & LIFE SPAN (AYURDAYA PRINCIPLES)"]

    h1 = all_houses.get("H1", {})
    h8 = all_houses.get("H8", {})
    lagna_lord = lagna.get("lord", "")
    ll = planets.get(lagna_lord, {})
    moon = planets.get("Moon", {})
    saturn = planets.get("Saturn", {})

    parts.append(f"Primary longevity indicators (BPHS Ayurdaya): the Lagna, Lagna lord, Moon, and 8th house together determine life span.")

    ll_h = ll.get("house", 0)
    ll_dg = ll.get("dignity", "neutral")
    if ll_h in (1, 4, 5, 7, 9, 10):
        parts.append(f"Lagna lord {lagna_lord} in H{ll_h} (kendra/trikona) with {ll_dg} dignity: "
                     + ("Excellent longevity indicator -- Lagna lord in a power house supports long life." if ll_dg in ("exalted","own_sign","moolatrikona")
                        else "Moderate longevity -- Lagna lord in angular/trine house is generally supportive of life span."))
    else:
        parts.append(f"Lagna lord {lagna_lord} in H{ll_h} ({ll_dg}): challenges to vitality; attention to health habits is strongly advised.")

    parts.append(f"Moon in H{moon.get('house',0)} ({moon.get('dignity','neutral')}): "
                 + ("Strong Moon supports mental and physical resilience, positively influencing longevity." if moon.get("dignity") in ("exalted","own_sign","moolatrikona")
                    else "Moon in challenging dignity may affect mental peace and overall vitality; consistent self-care advised."))

    parts.append(f"Saturn in H{saturn.get('house',0)} ({saturn.get('dignity','neutral')}): Saturn's role in the chart "
                 + ("strongly supports longevity -- Saturn in favourable dignity acts as a protector of life span." if saturn.get("dignity") in ("exalted","own_sign","moolatrikona")
                    else "suggests karmic delays and health challenges; preventive care and disciplined lifestyle are essential."))

    h8_strength = h8.get("strength", "moderate")
    parts.append(f"8th House (house of longevity): {h8_strength} strength. "
                 + ("Strong 8th house indicates resilience, good recovery from illness, and generally longer life span." if h8_strength == "strong"
                    else "Afflicted 8th house suggests caution around accidents, surgery, or sudden health events." if h8_strength == "weak"
                    else "Moderate 8th house; average longevity with attention to health in Saturn and Mars periods."))

    # Maraka warning
    h2_lord = all_houses.get("H2", {}).get("lord", "")
    h7_lord = all_houses.get("H7", {}).get("lord", "")
    parts.append(f"Note on maraka (life-inflicting) planets: {h2_lord} (lord of H2) and {h7_lord} (lord of H7) are traditional maraka planets. Their Mahadashas/Antardashas in advanced age should be monitored.")

    return "\n".join(f"  {p}" if i > 0 else p for i, p in enumerate(parts))


def _ordinal(n: int) -> str:
    suffixes = {1:"1st",2:"2nd",3:"3rd"}
    return suffixes.get(n, f"{n}th")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN EXPORT: generate_life_readings
# ═══════════════════════════════════════════════════════════════════════════════

def generate_life_readings(calc_result: dict) -> str:
    """
    Generate comprehensive life-area narrative readings from a kundli_calculator result dict.
    Returns a formatted multi-section text block to be appended to formatted_report.

    Args:
        calc_result: dict returned by compute_personal_kundli()

    Returns:
        str -- the life readings block (ready to append to formatted_report)
    """
    planets = calc_result.get("planets", {})
    lagna = calc_result.get("lagna", {})
    all_houses = calc_result.get("all_houses", {})
    dasha = calc_result.get("dasha", {})
    yogas = calc_result.get("yogas", [])

    if not planets or not lagna:
        return ""

    sep  = "=" * 52
    dash = "-" * 52
    lines: list[str] = []

    lines += ["", sep, "   COMPREHENSIVE LIFE READINGS", "   (BPHS | Phaladeepika | Saravali | Uttara Kalamrita)", sep, ""]

    sections = [
        _read_personality(planets, lagna, all_houses),
        _read_education(planets, lagna, all_houses),
        _read_career(planets, lagna, all_houses, dasha),
        _read_finance(planets, lagna, all_houses, yogas),
        _read_love_marriage(planets, lagna, all_houses, yogas),
        _read_children(planets, lagna, all_houses),
        _read_health(planets, lagna, all_houses),
        _read_home_family(planets, lagna, all_houses),
        _read_siblings(planets, lagna, all_houses),
        _read_father_fortune(planets, lagna, all_houses),
        _read_spirituality(planets, lagna, all_houses),
        _read_longevity(planets, lagna, all_houses),
        _read_current_period(planets, lagna, dasha),
    ]

    for section in sections:
        if not section.strip():
            continue
        first_line, *rest = section.split("\n")
        lines.append(f"{first_line}")
        lines.append(dash)
        for r in rest:
            lines.append(r)
        lines.append("")

    lines.append(sep)
    lines.append("  DISCLAIMER: Life readings are based on classical Vedic rules (BPHS etc.).")
    lines.append("  Planetary dignity, house placement, and dasha timing are computed,")
    lines.append("  not paraphrased. For major life decisions, consult a qualified Jyotishi.")
    lines.append(sep)

    return "\n".join(lines)
