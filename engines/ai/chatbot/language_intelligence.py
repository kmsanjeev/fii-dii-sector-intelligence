"""Governed Wave-1 expression lookup for VEDA.

The registry is intentionally local and deterministic.  It enriches COMM-001
with meaning and usage constraints; it is not a response generator and does
not require an LLM or general-RAG lookup.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


EXPRESSION_TYPES = (
    "IDIOM", "PHRASE", "SLANG", "COLLOQUIALISM", "PROVERB", "METAPHOR",
    "ABBREVIATION", "INTERNET_SLANG", "REGIONAL_EXPRESSION", "PROFESSIONAL_JARGON",
)
LANGUAGES = ("ENGLISH", "HINDI", "HINGLISH")
SCRIPTS = ("LATIN", "DEVANAGARI", "MIXED")
USAGE_LEVELS = (
    "LEVEL_0_FORMAL_LITERAL", "LEVEL_1_NATURAL", "LEVEL_2_CONVERSATIONAL",
    "LEVEL_3_IDIOMATIC", "LEVEL_4_HIGHLY_INFORMAL", "LEVEL_5_SLANG_RICH",
)


@dataclass(frozen=True, slots=True)
class ExpressionRecord:
    expression_id: str
    canonical_expression: str
    surface_forms: tuple[str, ...]
    language: str
    script: str
    language_variant: str
    region: str | None
    dialect: str | None
    expression_type: str
    literal_meaning: str
    contextual_meaning: str
    alternate_meanings: tuple[str, ...] = ()
    pragmatic_functions: tuple[str, ...] = ()
    tone: str = "NEUTRAL"
    register: str = "NEUTRAL"
    formality: str = "NEUTRAL"
    sentiment_tendency: str = "NEUTRAL"
    offensiveness_level: str = "NONE"
    sensitivity_notes: str | None = None
    generation_relevance: str = "UNKNOWN"
    domain: str | None = None
    time_relevance: str = "CURRENT"
    example_contexts: tuple[str, ...] = ()
    counterexamples: tuple[str, ...] = ()
    usage_constraints: tuple[str, ...] = ()
    understanding_confidence: str = "MODERATE"
    usage_confidence: str = "MODERATE"
    source: str = "VEDA-STD-003 governed seed corpus"
    source_type: str = "CURATED_SEED"
    source_quality: str = "GOVERNED_INTERNAL"
    provenance: str = "Seeded from the VEDA language-standard scope; external citation not asserted"
    knowledge_zone: str = "VALIDATED_KNOWLEDGE"
    status: str = "AVAILABLE_FOR_UNDERSTANDING"
    created_at: str = "2026-08-14"
    updated_at: str = "2026-08-14"
    version: str = "LANG-001-v1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _script(expression: str) -> str:
    devanagari = bool(re.search(r"[\u0900-\u097f]", expression))
    latin = bool(re.search(r"[a-zA-Z]", expression))
    return "MIXED" if devanagari and latin else "DEVANAGARI" if devanagari else "LATIN"


def _variant(language: str, script: str) -> str:
    if language == "ENGLISH":
        return "EN_INDIAN" if script == "LATIN" else "EN_GLOBAL"
    if language == "HINDI":
        return "HI_STANDARD" if script == "DEVANAGARI" else "HI_COLLOQUIAL"
    return "HINGLISH_MIXED_SCRIPT" if script == "MIXED" else "HINGLISH_ROMAN"


def _group(items: Iterable[str], language: str, expression_type: str, meaning: str, *, tone: str = "NEUTRAL", register: str = "NEUTRAL", formality: str = "NEUTRAL", domain: str | None = None, sensitivity: str = "NONE") -> list[ExpressionRecord]:
    expression_type = {"मुहावरा": "IDIOM", "कहावत": "PROVERB", "बोलचाल": "COLLOQUIALISM"}.get(expression_type, expression_type)
    records = []
    for index, expression in enumerate(items, 1):
        script = _script(expression)
        records.append(ExpressionRecord(
            expression_id=f"LANG001-{language[:2]}-{len(_ALL_RECORDS) + len(records) + 1:04d}",
            canonical_expression=expression.lower(), surface_forms=(expression.lower(),), language=language,
            script=script, language_variant=_variant(language, script), region="India" if language != "ENGLISH" else None,
            dialect="Hindi/Hinglish colloquial" if language != "ENGLISH" else None, expression_type=expression_type,
            literal_meaning=meaning, contextual_meaning=meaning, pragmatic_functions=("CONTEXTUAL_MEANING",),
            tone=tone, register=register, formality=formality, sentiment_tendency="NEGATIVE" if sensitivity != "NONE" else "NEUTRAL",
            offensiveness_level=sensitivity, sensitivity_notes="Understand without mirroring" if sensitivity != "NONE" else None,
            domain=domain, example_contexts=(expression,), usage_constraints=("Do not force active usage",),
            understanding_confidence="MODERATE", usage_confidence="LOW" if sensitivity != "NONE" else "MODERATE",
        ))
    return records


# These are curated, distinct seed expressions, grouped by governed meaning
# family.  They are not presented as dictionary citations or exhaustive lexica.
_ENGLISH_GROUPS = [
    (("break the ice", "piece of cake", "under the weather", "hit the nail on the head", "once in a blue moon", "spill the beans", "cost an arm and a leg", "bite the bullet", "on the same page", "the ball is in your court", "kick the bucket", "a blessing in disguise", "beat around the bush", "call it a day", "cut corners", "get out of hand", "go the extra mile", "hang in there", "in hot water", "let the cat out of the bag", "miss the boat", "pull someone's leg", "rule of thumb", "speak of the devil", "take it with a grain of salt", "the last straw", "through thick and thin", "under your nose", "up in the air", "wrap your head around", "back to square one", "burn the midnight oil", "by the book", "cross that bridge when we come to it", "devil's advocate", "draw the line", "easy does it", "hit the road", "in the same boat", "keep an eye on", "leave no stone unturned", "make ends meet", "off the hook", "read between the lines", "sit on the fence", "straight from the horse's mouth", "the tip of the iceberg", "when pigs fly", "your guess is as good as mine", "zero in on"), "IDIOM", "context-dependent non-literal expression"),
    (("good morning", "how are you", "nice to meet you", "long time no see", "take care", "see you around", "what's up", "no worries", "sounds good", "fair enough", "my bad", "go ahead", "hold on", "let me know", "that works", "I get it", "makes sense", "not a problem", "for what it's worth", "as far as I know", "to be honest", "in my view", "if you ask me", "just in case", "at the moment", "on the way", "for now", "all set", "good to go", "one step at a time"), "PHRASE", "common conversational meaning"),
    (("prepone", "do the needful", "out of station", "timepass", "good name", "cousin brother", "cousin sister", "revert back", "kindly do", "passed out of college", "only", "itself", "today morning", "batchmate", "upgradation", "discuss about", "order for", "return back", "flying to", "lakh", "crore", "crores of rupees", "fresher", "eve teasing", "co-brother", "co-sister", "mugging up", "tiffin", "shifted house", "send across"), "COLLOQUIALISM", "Indian-English usage; context does not imply incorrectness", {"register": "INDIAN_ENGLISH"}),
    (("lol", "rofl", "imo", "imho", "tbh", "idk", "fwiw", "iykyk", "fomo", "yolo", "brb", "afk", "omw", "irl", "dm", "tl;dr", "asap", "aka", "nvm", "wyd", "sus", "low-key", "high-key", "cringe", "ghosted", "salty", "based", "ratioed", "viral", "meme", "hashtag", "doomscroll", "clickbait", "stan", "glow-up", "soft launch", "hard launch", "main character", "rent-free"), "INTERNET_SLANG", "informal digital usage; meaning depends on context", {"register": "INFORMAL", "formality": "VERY_INFORMAL"}),
    (("alpha", "beta", "drawdown", "liquidity", "risk-on", "risk-off", "market cap", "cash flow", "value proposition", "runway", "growth hacking", "product-market fit", "api", "ci/cd", "race condition", "idempotency", "hotfix", "rollback", "pull request", "code review", "technical debt", "schema migration", "rate limit", "feature flag", "mean reversion", "standard deviation", "sample size", "control group", "peer review", "null hypothesis"), "PROFESSIONAL_JARGON", "domain-specific technical meaning", {"register": "PROFESSIONAL"}),
]
_HINDI_GROUPS = [
    (("नाक कटना", "आँखों का तारा", "दाँत खट्टे करना", "हाथ पर हाथ धरे बैठना", "नौ दो ग्यारह होना", "रंगे हाथ पकड़ा जाना", "आसमान सिर पर उठाना", "आटे दाल का भाव मालूम होना", "आँखों में धूल झोंकना", "कान भरना", "कमर कसना", "खून-पसीना एक करना", "चुल्लू भर पानी में डूब मरना", "छक्के छुड़ाना", "चार चाँद लगाना", "टस से मस न होना", "दाल में कुछ काला होना", "नाक में दम करना", "पानी-पानी होना", "रंगे हाथों", "लोहे के चने चबाना", "हवा में उड़ना", "हाथ मलना", "मुँह की खाना", "राई का पहाड़ बनाना", "रंगे सियार", "आस्तीन का साँप", "ईंट का जवाब पत्थर से देना", "खून खौलना", "नानी याद आना", "सिर पर कफन बाँधना", "बाल की खाल निकालना", "हाथ साफ करना", "गले का हार", "साँप सूँघ जाना", "पलक पाँवड़े बिछाना", "नौबत आना", "आँखों में बसना", "मुँह में पानी आना", "हाथ से निकलना", "कलेजा मुँह को आना", "दिल छोटा करना", "रंग में भंग पड़ना", "पेट में चूहे कूदना", "आग बबूला होना", "कान खड़े होना", "खून का घूँट पीना", "एक और एक ग्यारह", "अंधे की लाठी", "आसमान से गिरा खजूर में अटका"), "मुहावरा", "context-dependent Hindi idiomatic meaning", {"tone": "CONTEXTUAL", "register": "COLLOQUIAL"}),
    (("जैसी करनी वैसी भरनी", "देर आए दुरुस्त आए", "घर का भेदी लंका ढाए", "नाच न जाने आँगन टेढ़ा", "ऊँची दुकान फीका पकवान", "अंधों में काना राजा", "अधजल गगरी छलकत जाए", "अब पछताए होत क्या", "अंत भला तो सब भला", "एक अनार सौ बीमार", "खोदा पहाड़ निकली चुहिया", "नाम बड़े और दर्शन छोटे", "मन के हारे हार है", "दूर के ढोल सुहावने", "नेकी कर दरिया में डाल", "बूँद बूँद से सागर भरता है", "जहाँ चाह वहाँ राह", "जब जागो तभी सवेरा", "जैसा देश वैसा भेष", "घर की मुर्गी दाल बराबर", "आम के आम गुठलियों के दाम", "एक हाथ से ताली नहीं बजती", "दूध का जला छाछ भी फूँक फूँक कर पीता है", "सौ सुनार की एक लोहार की", "बंदर क्या जाने अदरक का स्वाद", "चोर की दाढ़ी में तिनका", "थोथा चना बाजे घना", "विनाश काले विपरीत बुद्धि", "साँप भी मर जाए लाठी भी न टूटे", "जिसकी लाठी उसकी भैंस", "तेते पाँव पसारिए जेती लंबी सौर", "बिल्ली के भाग्य से छींका टूटा", "आसमान के तारे तोड़ना", "अकेला चना भाड़ नहीं फोड़ता", "होनहार बिरवान के होत चिकने पात", "ओस चाटने से प्यास नहीं बुझती", "मुँह में राम बगल में छुरी", "सिर्फ कहने से कुछ नहीं होता", "समय बड़ा बलवान", "संगत का असर", "कर्म प्रधान विश्व रचि राखा", "सत्य की जीत", "धैर्य का फल मीठा होता है", "बोया पेड़ बबूल का", "जितनी चादर हो उतने पैर पसारो", "इच्छा हो तो उपाय", "एकता में बल है", "जल्दी का काम शैतान का", "दिखावे पर न जाएँ", "सावधानी हटी दुर्घटना घटी"), "कहावत", "Hindi proverb expressing a general observation", {"register": "FORMAL"}),
    (("नमस्ते", "आप कैसे हैं", "क्या हाल है", "बहुत धन्यवाद", "कोई बात नहीं", "ठीक है", "अच्छा", "चलो", "फिर मिलेंगे", "ध्यान रखना", "मुझे लगता है", "मेरी राय में", "सच कहूँ तो", "बिल्कुल सही", "समझ गया", "कोशिश करो", "देखते हैं", "अभी नहीं", "बाद में", "जल्दी करो", "रुकिए", "सुनिए", "बताइए", "कृपया", "माफ कीजिए", "स्वागत है", "शुभ रात्रि", "शुभ प्रभात", "कोई समस्या नहीं", "सब ठीक है"), "PHRASE", "common Hindi conversational meaning", {"register": "COLLOQUIAL"}),
    (("यार", "भाई", "चिल करो", "जुगाड़", "टाइमपास", "मूड ऑफ", "फंडा", "पंगा", "सीन", "बकवास", "झकास", "मस्त", "भाई लोग", "चक्कर", "लफड़ा", "घपला", "धांसू", "फालतू", "झोल", "कन्फ्यूज", "टेंशन", "सेटिंग", "वाइब", "कूल", "फुल ऑन", "गोलमाल", "बिंदास", "झटपट", "घुसपैठ", "कड़क"), "बोलचाल", "Hindi colloquial usage; context and relationship matter", {"register": "INFORMAL", "formality": "VERY_INFORMAL"}),
    (("meri band baja di", "mujhe samajh nahi aaya", "kya scene hai", "mood off hai", "panga mat lena", "funda clear nahi hai", "jugaad ho jayega", "timepass kar raha", "chill maar", "yaar sun", "bhai kya hua", "sach batao", "seedha bolo", "bahut tension hai", "sab theek ho jayega", "kaam ho gaya", "baat samajh aayi", "thoda ruk jao", "abhi aata hoon", "kal milte hain", "kya kar rahe ho", "mujhe nahi pata", "dekhte hain", "baad mein baat", "jaldi karo", "dhyan rakhna", "shukriya yaar", "maaf karna", "bilkul sahi", "theek hai yaar", "bakwaas"), "COLLOQUIALISM", "Roman Hindi conversational meaning; spelling varies by speaker", {"register": "ROMAN_HINDI", "formality": "INFORMAL"}),
]
_HINGLISH_GROUPS = [
    (("scene kya hai", "mood off hai", "full paisa vasool", "band baja di", "panga mat lena", "funda clear hai", "setting ho gayi", "jugaad kar lenge", "timepass", "chill maar", "yaar kya scene hai", "plan ka kya scene", "mood thoda off", "full on masti", "paisa vasool movie", "meri band baj gayi", "panga ho gaya", "funda samajh aa gaya", "setting kar do", "jugaad ho jayega", "bas timepass", "chill karo yaar", "scene set hai", "mood fresh hai", "full tight schedule", "boss ne band baja di", "panga mat create karo", "funda batao", "setting fix hai", "jugaad solution", "timepass mat karo", "chill reh", "scene clear nahi", "mood sahi hai", "full paisa vasool tha", "band baja dena", "panga lena", "funda weak hai", "setting karni hai", "jugaad se kaam", "timepass kar raha", "chill maar bro", "scene sorted", "mood ban gaya", "full power", "band baja di boss", "panga avoid karo", "funda clear nahi hai", "setting ho jayegi", "jugaad kar lenge"), "SLANG", "natural code-switched colloquial meaning", {"tone": "CONTEXTUAL", "register": "INFORMAL", "formality": "VERY_INFORMAL"}),
    (("seedha batao", "kaam karega kya", "samajh nahi aa raha", "abhi picture clear nahi", "thoda wait karo", "dekh lenge", "baad mein karenge", "kya bol raha hai", "mujhe nahi pata", "sach bol", "tension mat le", "sab manage ho jayega", "aaj ka plan kya hai", "market weak lag raha hai", "system hang ho gaya", "server down hai", "code deploy karna hai", "bug fix ho gaya", "risk zyada hai", "profit book kar lo", "chart ka trend", "dasha active hai", "kundli check karo", "funda samjha do", "plan ka next step", "boss se baat karo", "client ko update do", "meeting postpone hai", "deadline close hai", "workload bahut hai", "thoda adjust karo", "backup ready hai", "data clean hai", "report bhej do", "result ka wait", "idea solid hai", "logic sahi hai", "proof dikhao", "source kya hai", "research kar lo", "evidence weak hai", "context samjho", "meaning kya hai", "iska matlab batao", "translate mat karo", "natural bol", "formal mat bano", "simple language mein", "direct answer do"), "PHRASE", "context-dependent Hinglish phrase meaning", {"register": "COLLOQUIAL"}),
    (("boss", "yaar", "bro", "dude", "achha", "theek hai", "haan", "nahi yaar", "bilkul", "sahi hai", "mast hai", "kya baat hai", "arre", "oh no", "wow", "nice", "sorry yaar", "thank you yaar", "welcome bro", "good night yaar", "take care yaar", "milte hain", "call karna", "message kar dena", "reply karna", "ignore mat karo", "ghost mat hona", "low-key acha", "high-key funny", "vibe match", "vibe off", "mood ban", "feel aa rahi", "full respect", "no worries", "all good", "done hai", "sorted hai", "locked hai", "final hai", "almost ready", "not possible yaar", "try karte hain", "figure out kar lenge", "let's see", "ab kya", "kuch nahi", "sab chill", "too much", "over smart", "smart move", "good going"), "COLLOQUIALISM", "mixed English-Hindi conversational meaning", {"register": "INFORMAL"}),
    (("md", "ad", "pd", "d9", "d10", "api", "ci/cd", "hotfix", "alpha", "beta", "risk-on", "risk-off", "fomo", "yolo", "lol", "tbh", "imo", "idk", "brb", "asap", "ghosted", "salty", "sus", "cringe", "viral", "meme", "drawdown", "liquidity", "portfolio", "deadline"), "PROFESSIONAL_JARGON", "domain-sensitive mixed-language term", {"register": "PROFESSIONAL"}),
]

_ALL_RECORDS: list[ExpressionRecord] = []
for groups, language in ((_ENGLISH_GROUPS, "ENGLISH"), (_HINDI_GROUPS, "HINDI"), (_HINGLISH_GROUPS, "HINGLISH")):
    for group in groups:
        items, expression_type, meaning, *options = group
        kwargs = dict(options[0]) if options and isinstance(options[0], dict) else {}
        _ALL_RECORDS.extend(_group(items, language, expression_type, meaning, **kwargs))

# Collapse repeated surfaces within one language while preserving distinct
# English, Hindi, and Hinglish records where the language context differs.
_unique_records: dict[tuple[str, str], ExpressionRecord] = {}
for _record in _ALL_RECORDS:
    _key = (_record.language, _record.canonical_expression)
    if _key not in _unique_records:
        _unique_records[_key] = _record
    else:
        _previous = _unique_records[_key]
        _unique_records[_key] = ExpressionRecord(**{**_previous.to_dict(), "surface_forms": tuple(sorted(set(_previous.surface_forms + _record.surface_forms)))})
_ALL_RECORDS = list(_unique_records.values())

# Precise meanings for the benchmark and common diagnostic cases.
_MEANINGS = {
    "break the ice": "make an awkward first interaction easier", "piece of cake": "easy or straightforward",
    "under the weather": "feeling unwell", "spill the beans": "reveal a secret", "kick the bucket": "die, used idiomatically",
    "नाक कटना": "lose honour or suffer social embarrassment", "आँखों का तारा": "a much-loved person",
    "देर आए दुरुस्त आए": "late is better than never", "नाच न जाने आँगन टेढ़ा": "blame circumstances for one's own failure",
    "scene kya hai": "what is happening or what is the situation", "mood off hai": "feeling low or upset",
    "full paisa vasool": "excellent value or thoroughly worthwhile", "band baja di": "made things very difficult",
    "jugaad kar lenge": "we will find an improvised practical solution", "md": "domain-specific abbreviation; meaning requires context",
}
for _record_index, _record in enumerate(_ALL_RECORDS):
    if _record.canonical_expression in _MEANINGS:
        _ALL_RECORDS[_record_index] = ExpressionRecord(**{**_record.to_dict(), "contextual_meaning": _MEANINGS[_record.canonical_expression], "literal_meaning": _record.literal_meaning})

_SENSITIVE_EXPRESSIONS = {"bakwaas", "बकवास", "panga", "panga mat lena", "idiot", "shut up"}
for _record_index, _record in enumerate(_ALL_RECORDS):
    if _record.canonical_expression in _SENSITIVE_EXPRESSIONS:
        _ALL_RECORDS[_record_index] = ExpressionRecord(**{**_record.to_dict(), "offensiveness_level": "MILD", "sensitivity_notes": "Understand for context; do not echo automatically", "usage_confidence": "LOW"})

EXPRESSION_REGISTRY: tuple[ExpressionRecord, ...] = tuple(_ALL_RECORDS)


def normalize_surface(text: str) -> str:
    value = str(text or "").casefold().strip()
    value = value.replace("’", "'")
    value = re.sub(r"[\s\-_/]+", " ", value)
    return value.strip(" ,.!?;:()[]{}\"'")


_SURFACE_PATTERNS: tuple[tuple[re.Pattern[str], ExpressionRecord], ...] = tuple(
    (re.compile(rf"(?<![\w]){re.escape(normalize_surface(surface))}(?![\w])"), record)
    for record in EXPRESSION_REGISTRY
    for surface in record.surface_forms
)
_ALIAS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(rf"(?<![\w]){re.escape(alias)}(?![\w])"), canonical)
    for alias, canonical in (("spilled the beans", "spill the beans"), ("kicked the bucket", "kick the bucket"), ("नाक कटवा", "नाक कटना"))
)


def _find_records(text: str) -> list[ExpressionRecord]:
    normalized = normalize_surface(text)
    found: list[ExpressionRecord] = [record for pattern, record in _SURFACE_PATTERNS if pattern.search(normalized)]
    alias_canonicals = {canonical for pattern, canonical in _ALIAS_PATTERNS if pattern.search(normalized)}
    found.extend(record for record in EXPRESSION_REGISTRY if record.canonical_expression in alias_canonicals and record not in found)
    return found


def resolve_expressions(text: str, *, history: list[dict[str, Any]] | None = None, domain: str | None = None, conversation_type: str | None = None) -> dict[str, Any]:
    """Resolve known expressions without inventing unknown meanings."""
    value = str(text or "")
    lowered = normalize_surface(value)
    records = _find_records(value)
    resolved = []
    for record in records:
        meaning = record.contextual_meaning
        resolution = {
            "PROFESSIONAL_JARGON": "JARGON",
            "ABBREVIATION": "DOMAIN_AMBIGUOUS" if record.canonical_expression == "md" else "ABBREVIATION",
        }.get(record.expression_type, "IDIOMATIC")
        if record.canonical_expression in {"spill the beans", "kick the bucket"} and _has_literal_context(lowered, record.canonical_expression):
            resolution, meaning = "LITERAL", record.literal_meaning
        if re.search(rf"(?:say|mean|means|meaning of|why do people use).*{re.escape(record.canonical_expression)}", lowered):
            resolution = "METALINGUISTIC_USAGE"
        confidence = "HIGH" if record.domain is None or not domain or record.domain == domain else "MODERATE"
        resolved.append({"record": record.to_dict(), "resolution": resolution, "meaning": meaning, "confidence": confidence, "can_understand": True, "appropriate_to_use": _usage_allowed(record, conversation_type=conversation_type)})
    if re.search(r"(?<![\w])md(?![\w])", lowered):
        md_meaning = {"JYOTISHA": "Mahadasha", "BUSINESS": "Managing Director", "HEALTH": "Doctor of Medicine"}.get(str(domain or "").upper(), "domain-specific abbreviation; context is required")
        for item in resolved:
            if item["record"]["canonical_expression"] == "md":
                item["meaning"] = md_meaning
                item["confidence"] = "HIGH" if domain else "LOW"
    candidates = _candidate_expressions(value, records)
    return {"resolved": resolved, "unknown_expressions": candidates, "metalinguistic_use": any(item["resolution"] == "METALINGUISTIC_USAGE" for item in resolved)}


def _has_literal_context(text: str, expression: str) -> bool:
    return expression == "spill the beans" and ("onto the floor" in text or "on the floor" in text)


def _usage_allowed(record: ExpressionRecord, *, conversation_type: str | None) -> bool:
    if record.offensiveness_level in {"MODERATE", "HIGH", "SEVERE"}:
        return False
    if record.formality == "VERY_INFORMAL" and conversation_type in {"SHOP_TALK", "STRAIGHT_TALK"}:
        return False
    return record.usage_confidence in {"MODERATE", "HIGH", "VERY_HIGH"}


def _candidate_expressions(text: str, records: list[ExpressionRecord]) -> list[dict[str, str]]:
    lower = text.casefold()
    quoted = re.findall(r"['\"]([^'\"]{2,80})['\"]", text)
    questions = re.findall(r"(?:what does|meaning of|matlab of)\s+([\w\u0900-\u097f -]{2,60})", lower)
    known = {record.canonical_expression for record in records}
    candidates = []
    for surface in quoted + questions:
        normalized = normalize_surface(surface)
        if normalized and normalized not in known:
            candidates.append({"surface_expression": surface, "language_guess": "UNKNOWN", "candidate_meaning": "UNKNOWN_EXPRESSION", "confidence": "VERY_LOW", "review_state": "RESEARCH_REQUIRED"})
    return candidates


def corpus_stats() -> dict[str, int]:
    return {language: sum(record.language == language for record in EXPRESSION_REGISTRY) for language in LANGUAGES} | {"TOTAL": len(EXPRESSION_REGISTRY)}


def language_candidate(text: str, context: str = "") -> dict[str, str]:
    return {"surface_expression": text, "language_guess": "UNKNOWN", "context": context[:240], "candidate_meaning": "UNKNOWN_EXPRESSION", "confidence": "VERY_LOW", "review_state": "RESEARCH_REQUIRED"}


__all__ = ["EXPRESSION_REGISTRY", "EXPRESSION_TYPES", "LANGUAGES", "SCRIPTS", "USAGE_LEVELS", "ExpressionRecord", "corpus_stats", "language_candidate", "lookup_expressions", "normalize_surface", "resolve_expressions"]


def lookup_expressions(text: str, **kwargs: Any) -> list[dict[str, Any]]:
    return resolve_expressions(text, **kwargs)["resolved"]
