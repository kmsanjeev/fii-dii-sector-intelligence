# Jyotish exposure

The personal Kundli flow is wired from birth input through the personal tool,
the shared calculation path, chart facts, interpretation and Chat response.
The same family has API routes for human charts, stock/country charts, Gochar,
and UI surfaces in Chat, Report, Stocks and KundliCard.

Ordinary Jyotish concepts such as D9, D20, Nakshatra, Dasha, Shadbala and
Ashtakavarga are Chat-reachable through the ASTRO route. They are text/evidence
questions, not forced tool calls. D20 and source-limited strength claims remain
qualified. Generic `Lagna` currently routes to PERSONAL_KUNDLI even when no
personal birth input is present; this is a P1 routing gap because a conceptual
question can enter a personal-input path.

Muhurta has API routes and a Chat route, but `Panchanga`, natural auspicious
window language and ordinary house-entry language are not all recognized as
MUHURTA. This is underexposure, not a new Muhurta semantic implementation.
