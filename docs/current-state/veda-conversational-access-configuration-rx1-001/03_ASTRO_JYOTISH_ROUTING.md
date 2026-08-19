# Jyotish routing and tool separation

Ordinary Jyotish routes to `ASTROLOGY` and uses a qualified Jyotish prompt.
Generic Nakshatra, Dasha, D20, D9, Shadbala and Ashtakavarga questions remain
ordinary ASTRO questions. The prompt explicitly excludes market, capital-flow,
technical and AstroFinance framing unless the user asks for that context.

`ASTRO_FINANCE` is a separate capability because the existing
`get_astro_signal` behavior is a market-plus-astrology operation. Its tools are
available only for that route. ASTRO, GENERAL and MUHURTA receive no market
tools. `PERSONAL_KUNDLI` is separately owned by `KUNDLI` and keeps its own
generation tool and independent access toggle.

This is routing governance, not a new astrology engine.
