"""
Theme Intelligence Engine — Phase E (extended)
Aggregates stock-level intelligence into 50 themes, scoring each by
money flow (FII/DII), price momentum, and institutional conviction.

Now uses theme_tagging.csv (multi-theme) instead of single THEME column.
Purity scores weight each stock's contribution to a theme.

Run:
    py -3.11 engines/intelligence/theme_intelligence_engine.py

Output:
    data/intelligence/theme_intelligence.csv
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# ── Theme metadata — 50 themes ────────────────────────────────────────────────

THEME_META = {
    # ── Existing 15 (Phase D) ──────────────────────────────────────────────
    "CAPEX_CYCLE": {
        "display_name": "Capital Expenditure Boom",
        "category": "MACRO",
        "description": (
            "India's corporate and government capex supercycle — new factories, power plants, "
            "and industrial capacity being built at unprecedented scale."
        ),
        "macro_driver": "Government infra spend + PLI schemes + rising corporate profits",
        "risk": "Interest rate sensitivity, commodity cost inflation",
        "global_peer": "US Industrials, South Korea Steel cycle",
    },
    "CHINA_PLUS_ONE": {
        "display_name": "China+1 Manufacturing Shift",
        "category": "MACRO",
        "description": (
            "Global companies diversifying supply chains out of China into India — "
            "chemicals, electronics, and textiles lead this structural decade-long shift."
        ),
        "macro_driver": "Geopolitical realignment, PLI incentives, competitive labour costs",
        "risk": "Execution risk, infrastructure gaps, China export dumping",
        "global_peer": "Vietnam textiles, Taiwan semiconductors shift",
    },
    "FINANCIALISATION": {
        "display_name": "Financialisation of Savings",
        "category": "FINANCE",
        "description": (
            "Indians shifting savings from gold and real estate into stocks and MFs — "
            "financial companies see structural demand growth."
        ),
        "macro_driver": "Rising incomes, SIP culture, SEBI reforms, UPI credit ecosystem",
        "risk": "Market correction dampens SIP inflows, credit cycle stress",
        "global_peer": "US wealth management boom (2010-2020)",
    },
    "RURAL_CONSUMPTION": {
        "display_name": "Rural India Consumption",
        "category": "CONSUMER",
        "description": (
            "Rising rural incomes from better agri prices and government schemes "
            "driving demand for FMCG, two-wheelers, and agri inputs."
        ),
        "macro_driver": "Good monsoon, MSP hikes, MNREGA spend, rural credit growth",
        "risk": "Drought, inflation eroding real incomes",
        "global_peer": "Indonesia rural consumer cycle",
    },
    "DIGITAL_INDIA": {
        "display_name": "Digital India & Technology",
        "category": "TECHNOLOGY",
        "description": (
            "India's digital transformation — cloud adoption, fintech, digital payments, "
            "and IT services exports driving the next growth wave."
        ),
        "macro_driver": "UPI ecosystem, India Stack, AI adoption, US tech spend recovery",
        "risk": "INR appreciation, wage inflation, global tech slowdown",
        "global_peer": "Global AI infrastructure build (Nvidia, TSMC cycle)",
    },
    "HEALTHCARE_EXPANSION": {
        "display_name": "Healthcare & Pharma Growth",
        "category": "HEALTHCARE",
        "description": (
            "Healthcare spending rising as incomes grow — hospitals, pharma R&D, "
            "diagnostics, and health insurance all in structural upcycle."
        ),
        "macro_driver": "Post-COVID health awareness, ageing population, insurance penetration",
        "risk": "US FDA import alerts, pricing pressure on generics",
        "global_peer": "US Medicare expansion cycle",
    },
    "PREMIUMISATION": {
        "display_name": "Premium Consumption Upgrade",
        "category": "CONSUMER",
        "description": (
            "India's upper-middle class trading up — premium food, experiences, travel, "
            "and consumer goods seeing strong demand as aspirations rise."
        ),
        "macro_driver": "Rising urban incomes, aspirational class growth, credit availability",
        "risk": "Slowdown in discretionary spending during rate hike cycles",
        "global_peer": "China's premiumisation wave (2010-2015)",
    },
    "EV_TRANSITION": {
        "display_name": "Electric Vehicle Revolution",
        "category": "INFRA",
        "description": (
            "India's shift to electric mobility — EV makers, battery suppliers, "
            "charging infrastructure, and ancillaries all in early play."
        ),
        "macro_driver": "FAME subsidies, falling battery costs, fuel cost savings",
        "risk": "Technology disruption risk, raw material shortage (lithium)",
        "global_peer": "Tesla/BYD supply chain expansion",
    },
    "INFRASTRUCTURE_BUILD": {
        "display_name": "Infrastructure Buildout",
        "category": "INFRA",
        "description": (
            "Government's Rs 10 lakh crore annual infra push — roads, metro, ports, "
            "and urban infra creating a 7-10 year capex supercycle."
        ),
        "macro_driver": "National Infrastructure Pipeline (NIP), PPP revival, smart cities",
        "risk": "Land acquisition delays, liquidity stress in EPC companies",
        "global_peer": "US Infrastructure Act (2021), EU Green Deal",
    },
    "REAL_ESTATE_RECOVERY": {
        "display_name": "Real Estate Recovery",
        "category": "CONSUMER",
        "description": (
            "After a decade of stagnation, real estate is recovering — rising property "
            "prices, luxury housing boom, and office space demand returning."
        ),
        "macro_driver": "Inventory correction, WFH reversal, NRI buying, low unsold stock",
        "risk": "Rate hike affordability pressure, new supply influx",
        "global_peer": "Japan real estate recovery (2012-2019)",
    },
    "GREEN_ENERGY": {
        "display_name": "Green & Renewable Energy",
        "category": "ENERGY",
        "description": (
            "India targeting 500GW renewable capacity by 2030 — solar, wind, "
            "green hydrogen, and energy storage companies are direct beneficiaries."
        ),
        "macro_driver": "Global climate commitments, falling solar costs, energy security",
        "risk": "Land acquisition, grid curtailment, financing costs",
        "global_peer": "Global clean energy transition (IRA, European Green Deal)",
    },
    "LOGISTICS_MODERNISATION": {
        "display_name": "Logistics Modernisation",
        "category": "INFRA",
        "description": (
            "India's logistics costs (14% of GDP vs 8% globally) being tackled — "
            "warehousing, cold chain, and express delivery modernisation underway."
        ),
        "macro_driver": "GST e-waybill, PM Gati Shakti, Dedicated Freight Corridors",
        "risk": "Fragmented market, thin margins, fuel cost volatility",
        "global_peer": "Amazon logistics disruption, FedEx Asia expansion",
    },
    "DEFENCE_ELECTRONICS": {
        "display_name": "Defence & Aerospace",
        "category": "INDUSTRIAL",
        "description": (
            "India's indigenisation drive in defence — domestic manufacturers replacing "
            "imports in aerospace, missiles, naval systems, and electronics."
        ),
        "macro_driver": "Positive indigenisation lists, defence exports target, border tensions",
        "risk": "Long order-to-revenue cycles, technology transfer complexity",
        "global_peer": "US defence budget expansion, NATO spending surge",
    },
    "EXPORT_GROWTH": {
        "display_name": "Export & Global Trade",
        "category": "MACRO",
        "description": (
            "India gaining share in global exports — specialty chemicals, pharma APIs, "
            "textiles, and IT services are leading export vectors."
        ),
        "macro_driver": "Weak INR, global supply chain shifts, FTA negotiations",
        "risk": "Global demand slowdown, anti-dumping duties, INR strengthening",
        "global_peer": "Emerging market export cycles",
    },
    "PSU_REVIVAL": {
        "display_name": "Public Sector Revival",
        "category": "MACRO",
        "description": (
            "Government-owned companies being re-rated as governance improves — "
            "PSU banks, oil companies, and utilities recapturing investor attention."
        ),
        "macro_driver": "Government recapitalisation, dividend mandates, disinvestment re-think",
        "risk": "Government interference in business decisions, populist spending",
        "global_peer": "China SOE reform cycle",
    },

    # ── Phase E: 35 new themes ─────────────────────────────────────────────

    # Technology
    "DATA_CENTRE": {
        "display_name": "Data Centres & Cloud",
        "category": "TECHNOLOGY",
        "description": (
            "Hyperscaler capex (Azure, AWS, Google India) driving massive data centre buildout — "
            "AI inference demand requires low-latency local compute; India is a key site."
        ),
        "macro_driver": "AI workload growth, hyperscaler India investments, 5G data explosion",
        "risk": "Power availability, land cost escalation, hyperscaler concentration risk",
        "global_peer": "Equinix, Digital Realty, Iron Mountain global expansion",
    },
    "AI_ENABLERS": {
        "display_name": "Artificial Intelligence Enablers",
        "category": "TECHNOLOGY",
        "description": (
            "Indian companies enabling GenAI adoption — data annotation, AI services, "
            "IT companies landing AI-first deals, and GPU infra providers."
        ),
        "macro_driver": "GenAI enterprise adoption, India's data labelling advantage, AI deal TCV growth",
        "risk": "Technology disruption to existing IT services, margin compression",
        "global_peer": "Nvidia AI stack, Microsoft Copilot ecosystem",
    },
    "SEMICONDUCTOR": {
        "display_name": "Semiconductor & Electronics Mfg",
        "category": "TECHNOLOGY",
        "description": (
            "India Semiconductor Mission targeting domestic chip fabs — TATA-PSMC fab, "
            "Foxconn iPhone scale-up, PCB manufacturing, and electronic components."
        ),
        "macro_driver": "India Semiconductor Mission Rs 76K Cr, Apple India exports, PLI electronics",
        "risk": "Long gestation (10+ year fab cycle), raw material import dependency",
        "global_peer": "TSMC Taiwan, Samsung Korea fab expansion",
    },
    "FINTECH_INFRASTR": {
        "display_name": "Fintech Infrastructure",
        "category": "TECHNOLOGY",
        "description": (
            "UPI transaction volume doubling YoY, ONDC ecosystem, CBDC pilot, "
            "account aggregator — India building the world's most sophisticated payment rails."
        ),
        "macro_driver": "UPI volume 15B+ monthly, ONDC scaling, RBI CBDC pilot",
        "risk": "Regulatory tightening, cybersecurity threats, zero-MDR policy",
        "global_peer": "Stripe, PayPal, Brazil Pix payment rail ecosystem",
    },
    "CYBERSECURITY": {
        "display_name": "Cybersecurity & Data Protection",
        "category": "TECHNOLOGY",
        "description": (
            "DPDP Act 2023 compliance mandates + rising state-sponsored attacks + "
            "OT/SCADA security needs in energy/defence driving spend."
        ),
        "macro_driver": "DPDP Act compliance deadline, CERT-IN mandates, defence OT security",
        "risk": "SME budget constraints, global platform competition (Palo Alto, CrowdStrike)",
        "global_peer": "CrowdStrike, Zscaler, Palo Alto Networks global expansion",
    },

    # Infrastructure
    "POWER_TD": {
        "display_name": "Power Transmission & Distribution",
        "category": "INFRA",
        "description": (
            "Rs 3.03L Cr RDSS scheme + smart meter rollout 250M units + HVDC lines "
            "for RE evacuation — biggest power sector upgrade since independence."
        ),
        "macro_driver": "RDSS scheme, Revamped Distribution Sector, 250M smart meter mandate",
        "risk": "State DISCOM financial stress, payment delays, raw material (copper) costs",
        "global_peer": "ABB, Siemens Energy global grid upgrade cycle",
    },
    "WATER_MANAGEMENT": {
        "display_name": "Water & Sanitation",
        "category": "INFRA",
        "description": (
            "Jal Jeevan Mission Rs 3.6L Cr + water recycling mandates + drip irrigation "
            "boom + AMRUT 2.0 urban water supply — massive underserved opportunity."
        ),
        "macro_driver": "Jal Jeevan Mission, water stress in 21 major cities, ZLD mandates",
        "risk": "Execution risk in rural areas, state government payment delays",
        "global_peer": "Veolia, Xylem, Danaher global water infrastructure",
    },
    "RAILWAYS_METRO": {
        "display_name": "Railways & Metro Rail",
        "category": "INFRA",
        "description": (
            "Rs 2.5L Cr Vande Bharat expansion + metro rail in 50 cities + "
            "Dedicated Freight Corridors Phase 2 — largest railway modernisation globally."
        ),
        "macro_driver": "Vande Bharat 400 trains, DFC Phase 2, metro rail in 50+ cities",
        "risk": "Cost overruns, execution delays, land acquisition challenges",
        "global_peer": "Alstom, CRRC global railway equipment",
    },
    "PORTS_SHIPPING": {
        "display_name": "Ports & Maritime Logistics",
        "category": "INFRA",
        "description": (
            "Sagarmala Phase 3 + Vadhvan mega-port + India targeting global "
            "trans-shipment hub status — maritime logistics modernising rapidly."
        ),
        "macro_driver": "Sagarmala Rs 6L Cr, Vadhvan port, EXIM growth, India trade balance",
        "risk": "Global trade slowdown, congestion at major ports, geopolitical route disruption",
        "global_peer": "DP World, PSA International, Hutchison Ports expansion",
    },
    "SMART_CITIES": {
        "display_name": "Smart Cities & Urban Tech",
        "category": "INFRA",
        "description": (
            "Smart City Mission 2.0 + CCTV/surveillance rollout + traffic management "
            "systems + EV charging city infrastructure building."
        ),
        "macro_driver": "100 Smart Cities Mission, Rs 6,450 Cr AMRUT, urban population growth",
        "risk": "Implementation complexity, fragmented city-level procurement",
        "global_peer": "Honeywell, Bosch smart city solutions globally",
    },
    "GREEN_HYDROGEN": {
        "display_name": "Green Hydrogen Economy",
        "category": "ENERGY",
        "description": (
            "National Green Hydrogen Mission Rs 19,744 Cr — electrolyser manufacturing, "
            "green ammonia exports, and industrial decarbonisation."
        ),
        "macro_driver": "NGHM Rs 19,744 Cr, green ammonia export demand, decarbonisation mandates",
        "risk": "High cost vs grey hydrogen (4x), electrolyser technology risk, storage challenges",
        "global_peer": "ITM Power, Nel Hydrogen, Plug Power global electrolyser buildout",
    },

    # Financial Services
    "BANKING_CREDIT": {
        "display_name": "Banking & Credit Cycle",
        "category": "FINANCE",
        "description": (
            "Credit-to-GDP rising from 55% vs EM average 80% — banks, NBFCs, and MFIs "
            "riding a multi-year credit upcycle as India formalises."
        ),
        "macro_driver": "Credit-to-GDP gap, RBI rate cut cycle, SME lending boom",
        "risk": "Asset quality deterioration in unsecured loans, NBFC stress",
        "global_peer": "US banking credit cycle (2016-2019), Southeast Asia bank expansion",
    },
    "INSURANCE_GROWTH": {
        "display_name": "Insurance Penetration",
        "category": "FINANCE",
        "description": (
            "India's insurance penetration 4.2% vs global 7% — IRDAI reforms, "
            "mandatory health insurance push, and bancassurance growth drive the gap close."
        ),
        "macro_driver": "IRDAI Bima Sugam, mandatory health cover push, rising health awareness",
        "risk": "Claims ratio volatility, regulatory pricing caps, climate catastrophe events",
        "global_peer": "Southeast Asia insurance penetration catch-up story",
    },
    "WEALTH_MGMT": {
        "display_name": "Wealth Management & AMC",
        "category": "FINANCE",
        "description": (
            "MF AUM crossing Rs 70L Cr + PMS growth + demat accounts tripling — "
            "India's wealth management industry in structural upcycle."
        ),
        "macro_driver": "SIP Rs 26K Cr/month, demat 180M accounts, equity culture shift",
        "risk": "Market correction halting SIP inflows, regulatory fee compression",
        "global_peer": "Vanguard, BlackRock AUM growth trajectory (2000-2020)",
    },
    "MICROFINANCE": {
        "display_name": "Microfinance & Financial Inclusion",
        "category": "FINANCE",
        "description": (
            "PMJDY + Jan Suraksha + NBFC-MFI rural credit expansion — bringing "
            "300M unbanked Indians into formal credit for the first time."
        ),
        "macro_driver": "Financial inclusion mandates, PMJDY, rural credit gap Rs 30L Cr",
        "risk": "Portfolio at risk in stress events (COVID-like shocks), over-indebtedness",
        "global_peer": "Grameen Bank, SKS Microfinance, Latin America MFI expansion",
    },

    # Healthcare
    "HEALTHTECH": {
        "display_name": "Digital Health & Medtech",
        "category": "HEALTHCARE",
        "description": (
            "ABHA health ID ecosystem + teleconsultation boom + diagnostic aggregators "
            "+ AI radiology — India building digital health backbone."
        ),
        "macro_driver": "ABHA 640M registrations, Ayushman Bharat Digital Mission, AI radiology",
        "risk": "Data privacy concerns, regulatory uncertainty, doctor resistance",
        "global_peer": "Teladoc, Veeva Systems, Oscar Health global digital health",
    },
    "SPECIALTY_CHEM": {
        "display_name": "Specialty Chemicals & API",
        "category": "HEALTHCARE",
        "description": (
            "China exit from high-value chemical supply chains + import substitution "
            "in pharma APIs + fluorochemicals demand — India's chemical export opportunity."
        ),
        "macro_driver": "China+1 in chemicals, US FDA API import alerts on China, fluorine demand",
        "risk": "China dumping at low prices, capacity glut risk, raw material INR hedging",
        "global_peer": "BASF, Evonik, Lanxess specialty chemical cycle",
    },

    # Consumer
    "QUICK_COMMERCE": {
        "display_name": "Quick Commerce & D2C",
        "category": "CONSUMER",
        "description": (
            "Blinkit/Zepto/Swiggy Instamart dark store expansion + D2C brands bypassing "
            "traditional retail — new consumer commerce layer emerging."
        ),
        "macro_driver": "Urban convenience demand, smartphone penetration, D2C brand explosion",
        "risk": "Unit economics not proven at scale, dark store real estate cost, deep-pocketed competition",
        "global_peer": "Gorillas (Germany), Getir (Turkey) quick commerce global expansion",
    },
    "GOLD_JEWELLERY": {
        "display_name": "Gold & Precious Metals Retail",
        "category": "CONSUMER",
        "description": (
            "Organised jewellery gaining share from unorganised + GST compliance driving "
            "formalisation + wedding demand + sovereign gold bond alternatives."
        ),
        "macro_driver": "Organised market share rising from 35% to 60%, BIS hallmarking mandate",
        "risk": "Import duty changes, gold price correction, lab-grown diamond disruption",
        "global_peer": "Chow Tai Fook (HK), Signet Jewelers branded jewellery expansion",
    },
    "TOURISM_HOSP": {
        "display_name": "Tourism & Hospitality",
        "category": "CONSUMER",
        "description": (
            "Domestic tourism recovery + India as global spiritual and leisure destination "
            "+ G20 brand recognition + MICE (meetings/incentives) growth."
        ),
        "macro_driver": "Post-COVID pent-up demand, Incredible India 2.0, G20 brand lift",
        "risk": "Geopolitical events, weather disruption, overcapacity in hotel supply",
        "global_peer": "Marriott, Accor, OYO global travel recovery cycle",
    },
    "MEDIA_ENTERTAIN": {
        "display_name": "Media, Content & Entertainment",
        "category": "CONSUMER",
        "description": (
            "OTT consolidation + Indian cinema global expansion + sports IP monetisation "
            "+ gaming growth — content economy scaling fast."
        ),
        "macro_driver": "OTT subscriber growth, IPL media rights Rs 48K Cr, YouTube India",
        "risk": "Content cost inflation, piracy, OTT subscription fatigue",
        "global_peer": "Netflix, Disney streaming content war globally",
    },

    # Factor / Style
    "LARGECAP_VALUE": {
        "display_name": "Large Cap Value (>10K Cr mkt cap)",
        "category": "FACTOR",
        "description": (
            "Deep-value positioning in unloved large caps — PE below sector median, "
            "stable earnings, waiting for re-rating catalyst. Works in late bull cycles."
        ),
        "macro_driver": "Institutional rebalancing from growth to value in rising rate environments",
        "risk": "Value traps if earnings deteriorate; may underperform in strong bull markets",
        "global_peer": "Warren Buffett / Berkshire value approach, MSCI Value factor",
    },
    "MIDCAP_MOMENTUM": {
        "display_name": "Mid Cap Momentum (5K-25K Cr)",
        "category": "FACTOR",
        "description": (
            "Mid-cap stocks with 52W return >20%, above 200 DMA, volume expansion, "
            "and institutional buying — riding the mid-cap outperformance cycle."
        ),
        "macro_driver": "Mid-cap alpha vs Nifty 50 when risk appetite is positive",
        "risk": "Momentum reversal can be sharp; liquidity thinner than large caps",
        "global_peer": "NIFTY Midcap Momentum 30, Russell 2000 Momentum factor",
    },
    "SMALLCAP_QUALITY": {
        "display_name": "Small Cap Quality (<5K Cr)",
        "category": "FACTOR",
        "description": (
            "Hidden compounders: ROE >20%, Debt/Equity <0.5, promoter stake >50%, "
            "consistent earnings — small caps before institutional discovery."
        ),
        "macro_driver": "Bottom-up quality selection independent of macro cycle",
        "risk": "Illiquidity, discovery risk, governance risk in promoter-owned small caps",
        "global_peer": "NIFTY Smallcap Quality, VanEck Small Cap Quality ETF",
    },
    "DIVIDEND_YIELD": {
        "display_name": "High Dividend Yield",
        "category": "FACTOR",
        "description": (
            "Stocks with dividend yield >3.5%, sustainable payout ratio, preferred by "
            "FIIs for passive income — works as defensive play in risk-off markets."
        ),
        "macro_driver": "FII preference for yield, PSU dividend mandates, retiree allocation shift",
        "risk": "Dividend cuts if earnings deteriorate; yield trap in declining businesses",
        "global_peer": "FTSE Dividend Index, S&P Dividend Aristocrats",
    },
    "QUALITY_GROWTH": {
        "display_name": "Quality Growth Compounders",
        "category": "FACTOR",
        "description": (
            "ROCE >25%, 5Y revenue CAGR >15%, low leverage, consistent FCF — "
            "NIFTY QUALITY 50 type companies, priced at premium, rightfully."
        ),
        "macro_driver": "Long-term wealth compounders; sector-agnostic quality screen",
        "risk": "High valuation multiples vulnerable to growth deceleration",
        "global_peer": "MSCI Quality Factor, Morningstar Economic Moat companies",
    },
    "TURNAROUND": {
        "display_name": "Turnaround & Recovery",
        "category": "FACTOR",
        "description": (
            "Companies showing improving earnings from loss/low-profit base — "
            "restructuring, management change, or sector recovery signals."
        ),
        "macro_driver": "Post-distress recovery cycles; DII accumulation in beaten-down names",
        "risk": "False positives high; turnaround thesis can take 2-3 years to play out",
        "global_peer": "Distressed debt / special situations investing approach",
    },

    # Speculative / Emerging
    "SPACE_ECONOMY": {
        "display_name": "Space Economy",
        "category": "EMERGING",
        "description": (
            "IN-SPACe licensing unlocking private launch vehicles (Skyroot, Agnikul), "
            "satellite broadband, ISRO commercialisation — India space startup boom."
        ),
        "macro_driver": "IN-SPACe policy, 400+ space startups, government satellite orders",
        "risk": "Long gestation, high capex, technology risk, few listed pure plays",
        "global_peer": "SpaceX commercial satellite, Planet Labs earth observation",
    },
    "AGRITECH": {
        "display_name": "Agritech & Precision Farming",
        "category": "EMERGING",
        "description": (
            "Drone-based crop spraying + AI soil sensors + cold chain for perishables "
            "+ eNAM digital mandi — agriculture productivity tech exploding."
        ),
        "macro_driver": "Drone PLI Rs 120 Cr, eNAM 1,300 mandis, PM KUSUM solar pump",
        "risk": "Farmer adoption hurdles, seasonality, MNREGA competes for rural labour",
        "global_peer": "John Deere precision ag, Trimble agriculture, FBN agritech",
    },
    "BATTERY_STORAGE": {
        "display_name": "Battery & Energy Storage",
        "category": "EMERGING",
        "description": (
            "Grid-scale storage for RE intermittency + PLI for ACC batteries + "
            "pumped hydro revival + EV battery supply chain — multi-decade opportunity."
        ),
        "macro_driver": "PLI ACC Rs 18,100 Cr, RE grid storage mandate, EV battery localisation",
        "risk": "Technology disruption (solid-state vs lithium-ion), raw material supply",
        "global_peer": "CATL, LG Energy Solution, Panasonic battery expansion",
    },
    "GAMING_ESPORTS": {
        "display_name": "Gaming & Digital Entertainment",
        "category": "EMERGING",
        "description": (
            "India 2nd largest mobile gaming market + real-money gaming regulation "
            "+ esports Olympic roadmap + fantasy sports monetisation."
        ),
        "macro_driver": "450M mobile gamers, GST clarity on real-money gaming, esports recognition",
        "risk": "Regulatory overhang (TDS on winnings), addiction concerns, Google Play policies",
        "global_peer": "Sea Limited (Garena), Activision Blizzard Asia gaming expansion",
    },

    # Macro
    "INDIA_PLUS_ONE": {
        "display_name": "India as Global Alternative",
        "category": "MACRO",
        "description": (
            "India's emergence as the default alternative to China across manufacturing, "
            "services, and supply chains — structural multi-decade tailwind."
        ),
        "macro_driver": "China+1, US-India trade partnership, PLI scale-up, FDI inflows",
        "risk": "Infrastructure gaps, regulatory complexity, execution bandwidth",
        "global_peer": "Japan supply chain resilience fund, EU friend-shoring policies",
    },
    "INTEREST_RATE_CYCLE": {
        "display_name": "Interest Rate Cycle Play",
        "category": "MACRO",
        "description": (
            "RBI rate cut cycle benefiting rate-sensitive sectors — NIM expansion for "
            "banks, housing affordability improving, NBFC funding cost falling."
        ),
        "macro_driver": "RBI cut cycle, inflation trajectory, global Fed policy alignment",
        "risk": "Inflation resurgence forcing rate hike reversal, sticky core inflation",
        "global_peer": "US Fed rate cut cycle impact on banks, REITs, utilities",
    },
    "COMMODITY_SUPER": {
        "display_name": "Commodity Supercycle",
        "category": "ENERGY",
        "description": (
            "Structural shortage in critical minerals (copper, lithium, rare earths) "
            "as energy transition accelerates — metal and mining companies benefit."
        ),
        "macro_driver": "Energy transition critical minerals demand, China stockpiling, supply underinvestment",
        "risk": "China demand slowdown, substitution risk (less copper in solid-state batteries)",
        "global_peer": "BHP, Rio Tinto, Glencore commodity supercycle positioning",
    },
    "MONSOON_AGRI": {
        "display_name": "Monsoon & Agricultural Cycle",
        "category": "MACRO",
        "description": (
            "IMD monsoon forecast as annual alpha signal — kharif/rabi sowing data "
            "drives 3-month rural consumption outlook across FMCG, auto, banking."
        ),
        "macro_driver": "IMD rainfall cumulative, reservoir levels, kharif/rabi sowing area",
        "risk": "El Nino disruption, uneven spatial distribution, crop price volatility",
        "global_peer": "Brazil soy cycle, US corn belt weather-dependent trade",
    },
}


def _safe(v):
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _normalize(series: pd.Series, lo: float, hi: float) -> pd.Series:
    clipped = series.clip(lo, hi)
    return (clipped - lo) / (hi - lo)


def run():
    logger.info("[ThemeEngine] Starting Phase E theme intelligence engine (50 themes)")

    # ── Load data ──────────────────────────────────────────────────────────────
    tagging_path = cfg.REFERENCE_DIR / "theme_tagging.csv"
    clf_path     = cfg.REFERENCE_DIR / "company_classification_v4.csv"
    bull_path    = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
    pm_path      = cfg.INTELLIGENCE_DIR / "price_momentum.csv"
    sr_path      = cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
    ml_path      = cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv"

    for p in [bull_path, pm_path, sr_path]:
        if not p.exists():
            logger.error(f"[ThemeEngine] Missing required file: {p}")
            return

    # Prefer multi-theme tagging; fall back to single-theme classification
    if tagging_path.exists():
        tagging = pd.read_csv(tagging_path)
        tagging.columns = [c.upper() for c in tagging.columns]
        logger.info(f"[ThemeEngine] Using theme_tagging.csv: {len(tagging)} tags, "
                    f"{tagging['THEME'].nunique()} themes")
    else:
        logger.warning("[ThemeEngine] theme_tagging.csv not found — falling back to classification_v4")
        clf = pd.read_csv(clf_path)
        clf.columns = [c.upper() for c in clf.columns]
        tagging = clf[["SYMBOL", "THEME", "SECTOR"]].copy()
        tagging["PURITY_SCORE"] = 1.0
        tagging["IS_PRIMARY"]   = True

    bull = pd.read_csv(bull_path)
    pm   = pd.read_csv(pm_path)
    sr   = pd.read_csv(sr_path)
    ml   = pd.read_csv(ml_path) if ml_path.exists() else None

    bull["symbol"] = bull["symbol"].str.upper()
    pm["symbol"]   = pm["symbol"].str.upper()

    stock_df = bull.merge(
        pm[["symbol", "ret_30d", "ret_60d", "ret_90d", "ret_365d", "vol_ratio"]],
        on="symbol", how="left", suffixes=("", "_pm")
    )
    if ml is not None:
        ml["symbol"] = ml["symbol"].str.upper()
        stock_df = stock_df.merge(
            ml[["symbol", "ml_bull_run_score", "accumulation_score"]],
            on="symbol", how="left"
        )

    sr_latest = sr.copy()
    sr_latest["sector"] = sr_latest["sector"].str.upper()

    tagging["SYMBOL"] = tagging["SYMBOL"].str.upper()
    tagging["THEME"]  = tagging["THEME"].str.upper()

    results = []

    for theme_code, meta in THEME_META.items():
        # Stocks tagged to this theme
        theme_tags = tagging[tagging["THEME"] == theme_code][["SYMBOL", "PURITY_SCORE", "SECTOR"]].copy()
        if theme_tags.empty:
            logger.warning(f"[ThemeEngine] No stocks for theme: {theme_code}")
            continue

        # Merge with stock intelligence
        ts_df = theme_tags.merge(stock_df, left_on="SYMBOL", right_on="symbol", how="inner")
        if ts_df.empty:
            continue

        # Purity-weighted aggregation
        w = ts_df["PURITY_SCORE"].clip(0.01, 1.0)

        def wavg(col: str):
            if col not in ts_df.columns:
                return None
            vals = pd.to_numeric(ts_df[col], errors="coerce")
            mask = vals.notna()
            if mask.sum() == 0:
                return None
            return float((vals[mask] * w[mask]).sum() / w[mask].sum())

        stock_count   = len(ts_df)
        scored_count  = ts_df["bull_run_score"].notna().sum()
        label_counts  = ts_df["label"].value_counts().to_dict() if "label" in ts_df.columns else {}
        # Taxonomy fix (Phase V-DATA-2): STRONG_CANDIDATE was replaced by
        # BULL_RUN a while back -- this counter has been reading 0 since.
        strong_count  = label_counts.get("BULL_RUN", 0)
        emerging_count = label_counts.get("EMERGING", 0)

        avg_bull     = wavg("bull_run_score")
        avg_ret_30d  = wavg("ret_30d")
        avg_ret_60d  = wavg("ret_60d")
        avg_ret_90d  = wavg("ret_90d")
        avg_ret_365d = wavg("ret_365d")
        avg_vol_ratio = wavg("vol_ratio")
        avg_ml_score  = wavg("ml_bull_run_score")
        avg_accum     = wavg("accumulation_score")

        # Sector flow signals for this theme's sectors
        theme_sectors = ts_df["SECTOR"].dropna().str.upper().unique().tolist()
        sector_rows = sr_latest[sr_latest["sector"].isin(theme_sectors)]

        fii_flow      = float(sector_rows["FII_flow_score"].mean())   if not sector_rows.empty and "FII_flow_score"   in sector_rows.columns else None
        dii_flow      = float(sector_rows["DII_flow_score"].mean())   if not sector_rows.empty and "DII_flow_score"   in sector_rows.columns else None
        smart_money   = float(sector_rows["Smart_Money_Score"].mean()) if not sector_rows.empty and "Smart_Money_Score" in sector_rows.columns else None
        price_mom_sec = float(sector_rows["price_momentum_score"].mean()) if not sector_rows.empty and "price_momentum_score" in sector_rows.columns else None

        # Composite theme score (0-100)
        c1 = _normalize(pd.Series([avg_bull or 0]), 20, 60).iloc[0]              # 35%
        c2 = _normalize(pd.Series([smart_money or 0]), -50, 30).iloc[0]          # 30%
        c3 = _normalize(pd.Series([avg_ret_365d or 0]), -30, 60).iloc[0]         # 20%
        c4 = _normalize(pd.Series([avg_ret_30d or 0]), -10, 15).iloc[0]          # 15%
        theme_score = round((0.35 * c1 + 0.30 * c2 + 0.20 * c3 + 0.15 * c4) * 100, 2)

        # Momentum phase
        r30  = avg_ret_30d or 0
        r90  = avg_ret_90d or 0
        r1y  = avg_ret_365d or 0
        if r30 > 5 and r30 > (r90 / 3 + 1):
            momentum_phase = "ACCELERATING"
        elif r30 > 2 and r1y > 15:
            momentum_phase = "MOMENTUM"
        elif r30 > 0 and r1y < 5:
            momentum_phase = "EARLY_ROTATION"
        elif r30 < -2 and r1y > 10:
            momentum_phase = "DECELERATING"
        elif r1y < -10:
            momentum_phase = "DORMANT"
        else:
            momentum_phase = "CONSOLIDATING"

        # Theme signal
        sm = smart_money or 0
        if sm > 10 and r30 > 3:
            theme_signal = "HEATING_UP"
        elif sm > 0 and r1y > 15:
            theme_signal = "MOMENTUM"
        elif sm > 0 and r30 > 0:
            theme_signal = "BUILDING"
        elif sm < -20 and r30 > 3:
            theme_signal = "PRICE_LED"
        elif sm < -15 and r30 < -2:
            theme_signal = "DISTRIBUTION"
        else:
            theme_signal = "NEUTRAL"

        # Participant leader
        fii_v = fii_flow or 0
        dii_v = dii_flow or 0
        if fii_v > 0 and fii_v > dii_v:
            participant_leader = "FII"
        elif dii_v > 0 and dii_v >= fii_v:
            participant_leader = "DII"
        elif sm > 0:
            participant_leader = "SMART_MONEY"
        else:
            participant_leader = "RETAIL"

        # Top picks by purity-weighted bull score
        ts_df["_wscore"] = ts_df["bull_run_score"] * ts_df["PURITY_SCORE"]
        top_picks_df = ts_df.nlargest(5, "_wscore")[["symbol", "bull_run_score", "label", "PURITY_SCORE"]].copy()
        top_picks_df = top_picks_df.rename(columns={"PURITY_SCORE": "purity_score"})
        top_picks = top_picks_df.to_dict(orient="records")

        sectors_str = ",".join(sorted(set(theme_sectors)))

        results.append({
            "theme":              theme_code,
            "display_name":       meta["display_name"],
            "category":           meta.get("category", "OTHER"),
            "description":        meta["description"],
            "macro_driver":       meta["macro_driver"],
            "risk_factor":        meta["risk"],
            "global_peer":        meta["global_peer"],
            "sectors":            sectors_str,
            "stock_count":        stock_count,
            "scored_count":       int(scored_count),
            "strong_count":       int(strong_count),
            "emerging_count":     int(emerging_count),
            "theme_score":        _safe(theme_score),
            "theme_signal":       theme_signal,
            "momentum_phase":     momentum_phase,
            "participant_leader": participant_leader,
            "avg_bull_score":     round(float(avg_bull), 2) if avg_bull is not None else None,
            "avg_ret_30d":        round(float(avg_ret_30d), 2) if avg_ret_30d is not None else None,
            "avg_ret_60d":        round(float(avg_ret_60d), 2) if avg_ret_60d is not None else None,
            "avg_ret_90d":        round(float(avg_ret_90d), 2) if avg_ret_90d is not None else None,
            "avg_ret_365d":       round(float(avg_ret_365d), 2) if avg_ret_365d is not None else None,
            "avg_vol_ratio":      round(float(avg_vol_ratio), 2) if avg_vol_ratio is not None else None,
            "avg_ml_score":       round(float(avg_ml_score), 2) if avg_ml_score is not None else None,
            "avg_accum_score":    round(float(avg_accum), 2) if avg_accum is not None else None,
            "fii_flow_score":     round(float(fii_flow), 2) if fii_flow is not None else None,
            "dii_flow_score":     round(float(dii_flow), 2) if dii_flow is not None else None,
            "smart_money_score":  round(float(smart_money), 2) if smart_money is not None else None,
            "price_sector_momentum": round(float(price_mom_sec), 2) if price_mom_sec is not None else None,
            "top_picks":          json.dumps(top_picks),
            "as_of_date":         pd.Timestamp.now().strftime("%Y-%m-%d"),
        })

        logger.info(f"[ThemeEngine] {theme_code}: score={theme_score:.1f} signal={theme_signal} "
                    f"stocks={stock_count} purity_weighted")

    if not results:
        logger.error("[ThemeEngine] No theme results generated")
        return

    out_df = pd.DataFrame(results).sort_values("theme_score", ascending=False).reset_index(drop=True)
    out_path = cfg.INTELLIGENCE_DIR / "theme_intelligence.csv"
    tmp_path = out_path.with_suffix(".tmp")
    out_df.to_csv(tmp_path, index=False)
    import shutil
    shutil.move(str(tmp_path), str(out_path))

    logger.info(f"[ThemeEngine] Wrote {len(out_df)} themes to {out_path}")

    print(f"\n[ThemeEngine] Phase E complete: {len(out_df)} themes scored")
    print(f"{'RANK':<5} {'THEME':<30} {'SCORE':>6}  {'SIGNAL':<14} {'STOCKS':>6}  {'PHASE'}")
    print("-" * 80)
    for i, r in out_df.iterrows():
        print(f"{i+1:<5} {r['theme']:<30} {r['theme_score']:>6.1f}  {r['theme_signal']:<14} {r['stock_count']:>6}  {r['momentum_phase']}")

    return out_df


if __name__ == "__main__":
    run()
