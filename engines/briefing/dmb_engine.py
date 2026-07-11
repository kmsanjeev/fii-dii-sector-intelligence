"""
Daily Market Brief (DMB) Engine
Phase DMB-1 -- Assembles the pre-market institutional briefing note.

Reads every relevant intelligence output (all read-only, G-D-01), renders a
full markdown report in the institutional reading order, adds a data-locked
AI synthesis (executive summary + AI intelligence section), saves it to
data/reports/DMB_YYYY-MM-DD.md and delivers to Telegram (digest message +
the full report as an attached document).

HONESTY RULE: a missing source renders as "N/A -- <reason>". The DMB never
invents a number. Deferred sections (macro calendar, IPO/GMP, analyst
ratings) say so explicitly.

Run full chain:  py -3.11 -m engines.briefing.dmb_engine
(runs global snapshot + breadth + index options first, then assembles)
"""

import shutil
import sys
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

REPORTS_DIR = cfg.DATA_DIR / "reports"
I = cfg.INTELLIGENCE_DIR

SRC = {
    "global":      I / "global_snapshot.csv",
    "breadth":     I / "market_breadth.csv",
    "options":     I / "index_options.csv",
    "participant": I / "participant_intelligence.csv",
    "sector":      I / "sector_rotation_intelligence.csv",
    "conviction":  I / "conviction_screener.csv",
    "trade_conv":  I / "trade_conviction_scores.csv",
    "technical":   I / "technical_indicators.csv",
    "deals":       I / "institutional_deal_signals.csv",
    "events":      I / "event_calendar.csv",
    "news":        I / "news_signals.csv",
    "insider":     I / "insider_signals.csv",
    "bull_watch":  I / "bull_run_watchlist.csv",
}


def _read(name: str) -> pd.DataFrame | None:
    p = SRC[name]
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
        return df if not df.empty else None
    except Exception as e:
        logger.warning("[DMB] %s unreadable: %s", p.name, e)
        return None


def _fmt_chg(v) -> str:
    if v is None or pd.isna(v):
        return "n/a"
    return f"{'+' if v >= 0 else ''}{v:.2f}%"


class DMBEngine:
    """Renders and delivers the Daily Market Brief."""

    def __init__(self):
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.today = date.today()
        self.facts: list[str] = []       # compiled fact sheet for the AI pass
        self.bias: dict = {}             # deterministic bias inputs

    # ── Assembly ──────────────────────────────────────────────────────────────

    def run(self, deliver: bool = True) -> bool:
        logger.info("[DMB] Assembling brief for %s", self.today)
        parts: list[str] = []
        parts += [f"# DAILY MARKET BRIEF -- {self.today.strftime('%A, %d %B %Y')}",
                  f"Generated {datetime.now(timezone.utc).strftime('%H:%M UTC')} | "
                  f"Capital Flow Intelligence Platform", ""]

        sec_global   = self._sec_global()
        sec_flows    = self._sec_flows()
        sec_options  = self._sec_options()
        sec_sector   = self._sec_sector()
        sec_tech     = self._sec_technicals()
        sec_corp     = self._sec_corporate()
        sec_scanner  = self._sec_scanner()
        sec_risk     = self._sec_risk()
        sec_plan     = self._sec_plan()
        ai_exec, ai_intel = self._ai_synthesis()

        parts += ["## 1. EXECUTIVE SUMMARY", "", ai_exec, ""]
        parts += sec_global + sec_flows + sec_options + sec_sector
        parts += sec_tech + sec_corp + sec_scanner + sec_risk + sec_plan
        parts += ["## 15. AI MARKET INTELLIGENCE", "", ai_intel, ""]
        parts += ["---", "Deferred (no trustworthy free source wired): "
                  "macro-event calendar, IPO/GMP, analyst ratings, India 10Y "
                  "yield, GIFT Nifty premium, delivery %. These are never "
                  "fabricated. See docs/modules/DAILY_MARKET_BRIEF.md.",
                  "", "DISCLAIMER: informational only, not investment advice."]

        report = "\n".join(parts)
        out = REPORTS_DIR / f"DMB_{self.today.isoformat()}.md"
        tmp = out.with_suffix(".tmp.md")                          # G-D-02
        tmp.write_text(report, encoding="utf-8")
        shutil.move(str(tmp), str(out))
        logger.info("[DMB] Report written: %s (%d chars)", out.name, len(report))

        if deliver:
            self._deliver(out, ai_exec)
        return True

    # ── Sections ──────────────────────────────────────────────────────────────

    def _sec_global(self) -> list[str]:
        out = ["## 2. OVERNIGHT GLOBAL MARKETS", ""]
        g = _read("global")
        if g is None:
            return out + ["N/A -- global snapshot unavailable", ""]
        ok = g[g["status"] == "OK"]

        def block(title, group):
            rows = ok[ok["group"] == group]
            if rows.empty:
                return [f"**{title}**: N/A"]
            lines = [f"**{title}**"]
            for _, r in rows.iterrows():
                lines.append(f"- {r['name']}: {r['last']:,.1f} ({_fmt_chg(r['chg_pct'])})")
            return lines

        for title, grp in [("US (overnight close)", "US"), ("Europe", "EUROPE"),
                           ("Asia (this morning)", "ASIA"), ("US Futures (now)", "FUTURES")]:
            out += block(title, grp) + [""]

        # Biggest mover
        if not ok.empty:
            idx_only = ok[ok["group"].isin(["US", "EUROPE", "ASIA"])].dropna(subset=["chg_pct"])
            if not idx_only.empty:
                big = idx_only.loc[idx_only["chg_pct"].abs().idxmax()]
                out += [f"Biggest overnight mover: **{big['name']} {_fmt_chg(big['chg_pct'])}**", ""]
                self.facts.append(f"biggest global mover {big['name']} {_fmt_chg(big['chg_pct'])}")

        avg = ok[ok["group"].isin(["US", "ASIA", "FUTURES"])]["chg_pct"].mean()
        self.bias["global_avg_chg"] = float(avg) if pd.notna(avg) else 0.0
        self.facts.append(f"global average change {_fmt_chg(avg)}")

        out += ["## 3. GIFT NIFTY / OPENING CUE", "",
                "GIFT Nifty: N/A on free feeds -- using US futures + Asia as the opening cue.", ""]
        out += ["## 4. COMMODITIES / CURRENCY / BONDS / VOLATILITY", ""]
        for title, grp in [("Commodities", "COMMODITY"), ("Currency", "CURRENCY"),
                           ("Bonds", "BOND"), ("Volatility", "VOLATILITY")]:
            out += block(title, grp) + [""]
        out += ["India 10Y yield: N/A -- no free feed wired.", ""]

        vix = ok[ok["name"] == "India VIX"]
        if not vix.empty:
            v = float(vix.iloc[0]["last"])
            self.bias["india_vix"] = v
            self.facts.append(f"India VIX {v:.1f}")
        usdinr = ok[ok["name"] == "USD/INR"]
        if not usdinr.empty:
            self.facts.append(f"USDINR {usdinr.iloc[0]['last']} ({_fmt_chg(usdinr.iloc[0]['chg_pct'])})")
        crude = ok[ok["name"] == "Brent Crude"]
        if not crude.empty:
            self.facts.append(f"Brent {crude.iloc[0]['last']} ({_fmt_chg(crude.iloc[0]['chg_pct'])})")
        return out

    def _sec_flows(self) -> list[str]:
        out = ["## 5. FII / DII FLOWS", ""]
        p = _read("participant")
        if p is None:
            return out + ["N/A -- participant intelligence unavailable", ""]
        p = p.sort_values("date")
        last = p.iloc[-1]
        regime = str(last.get("Market_Regime", "UNKNOWN"))
        self.bias["regime"] = regime
        fii = last.get("FII_flow_score"); dii = last.get("DII_flow_score")
        smart = last.get("Smart_Money_Score")
        div = last.get("FII_DII_Divergence")
        out += [f"- Regime: **{regime}** (as of {last.get('date')})",
                f"- FII flow score: {fii} | DII flow score: {dii}",
                f"- Smart money score: {smart} | FII-DII divergence: {div}"]
        for win, label in [(5, "5-day"), (20, "20-day")]:
            tail = p.tail(win)
            if "FII_flow_score" in tail.columns and len(tail) >= 2:
                out.append(f"- {label} trend: FII avg "
                           f"{pd.to_numeric(tail['FII_flow_score'], errors='coerce').mean():.1f} | "
                           f"DII avg {pd.to_numeric(tail['DII_flow_score'], errors='coerce').mean():.1f}")
        out.append("")
        self.facts.append(f"regime {regime}, FII score {fii}, DII score {dii}, smart money {smart}")
        return out

    def _sec_options(self) -> list[str]:
        out = ["## 6. F&O AND OPTIONS POSITIONING", ""]
        o = _read("options")
        if o is None:
            return out + ["N/A -- index options unavailable", ""]
        for idx in ("NIFTY", "BANKNIFTY"):
            d = o[o["index"] == idx].set_index("key")["value"]
            if d.empty:
                continue
            out += [f"**{idx}** (expiry {o[o['index'] == idx]['expiry'].iloc[0]})",
                    f"- Spot {d.get('spot')} | PCR {d.get('pcr')} | Max pain {d.get('max_pain')}",
                    f"- Support {d.get('support')} (put wall) | Resistance {d.get('resistance')} (call wall)",
                    f"- Expected range: **{d.get('expected_range')}**",
                    f"- Call OI walls: {d.get('top_call_oi_strikes')}",
                    f"- Put OI walls: {d.get('top_put_oi_strikes')}",
                    f"- Futures read: **{d.get('futures_read')}** | "
                    f"chain OI chg C {d.get('call_oi_change')} / P {d.get('put_oi_change')}", ""]
            if idx == "NIFTY":
                self.bias["pcr"] = d.get("pcr")
                self.bias["nifty_range"] = d.get("expected_range")
                self.facts.append(f"NIFTY PCR {d.get('pcr')}, max pain {d.get('max_pain')}, "
                                  f"range {d.get('expected_range')}, futures {d.get('futures_read')}")
        return out

    def _sec_sector(self) -> list[str]:
        out = ["## 7. SECTOR ROTATION (INSTITUTIONAL MONEY FLOW)", ""]
        s = _read("sector")
        if s is None:
            return out + ["N/A", ""]
        s = s.copy()
        s["combined_score"] = pd.to_numeric(s.get("combined_score"), errors="coerce")
        s = s.dropna(subset=["combined_score"]).sort_values("combined_score", ascending=False)
        strong = s.head(5); weak = s.tail(5)
        out.append("**Money moving in:**")
        out += [f"- ^ {r['sector']} (score {r['combined_score']:.1f}, {r.get('rotation_signal','')})"
                for _, r in strong.iterrows()]
        out.append("")
        out.append("**Money moving out:**")
        out += [f"- v {r['sector']} (score {r['combined_score']:.1f}, {r.get('rotation_signal','')})"
                for _, r in weak.iterrows()]
        out.append("")
        self.facts.append("strong sectors: " + ", ".join(strong["sector"].head(3)))
        self.facts.append("weak sectors: " + ", ".join(weak["sector"].tail(3)))
        self.bias["top_sectors"] = list(strong["sector"].head(3))
        self.bias["weak_sectors"] = list(weak["sector"].tail(3))
        return out

    def _sec_technicals(self) -> list[str]:
        out = ["## 8. TECHNICAL STRUCTURE & BREADTH", ""]
        b = _read("breadth")
        if b is None:
            return out + ["N/A", ""]
        for idx in ("NIFTY", "BANKNIFTY"):
            d = b[b["metric_type"] == f"INDEX_{idx}"].set_index("key")["value"]
            if d.empty or "last" not in d.index:
                out += [f"**{idx}**: N/A", ""]
                continue
            out += [f"**{idx}**: {d.get('last')} | trend {d.get('trend')} | "
                    f"RSI {d.get('rsi_14')} | MACD {d.get('macd')}",
                    f"- DMA 20/50/200: {d.get('dma_20')} / {d.get('dma_50')} / {d.get('dma_200')}",
                    f"- Support {d.get('support')} | Resistance {d.get('resistance')}", ""]
            if idx == "NIFTY":
                self.bias["nifty_trend"] = d.get("trend")
                self.facts.append(f"NIFTY {d.get('last')} trend {d.get('trend')} RSI {d.get('rsi_14')}")
        br = b[b["metric_type"] == "BREADTH"].set_index("key")["value"]
        if not br.empty:
            out += ["**Yesterday's breadth:**",
                    f"- Advances {br.get('advances')} / Declines {br.get('declines')} "
                    f"(A/D {br.get('ad_ratio')}) | Up/Down volume {br.get('up_down_volume_ratio')}",
                    f"- Near 52w high: {br.get('near_52w_high')} | near 52w low: {br.get('near_52w_low')}",
                    f"- Turnover ~ {br.get('turnover_cr')} cr | Delivery %: N/A (not in cache schema)", ""]
            try:
                self.bias["ad_ratio"] = float(br.get("ad_ratio"))
            except (TypeError, ValueError):
                pass
            self.facts.append(f"breadth A/D {br.get('ad_ratio')}, up/down vol {br.get('up_down_volume_ratio')}")
        return out

    def _sec_corporate(self) -> list[str]:
        out = ["## 9. CORPORATE ACTIONS, EARNINGS, NEWS, DEALS, INSIDERS", ""]
        ev = _read("events")
        if ev is not None and "event_date" in ev.columns:
            ev["_d"] = pd.to_datetime(ev["event_date"], errors="coerce").dt.date
            today_ev = ev[ev["_d"] == self.today]
            week_ev = ev[(ev["_d"] > self.today) & (ev["_d"] <= self.today + timedelta(days=7))]
            out.append(f"**Events today ({len(today_ev)}):**")
            for _, r in today_ev.head(12).iterrows():
                out.append(f"- {r.get('symbol','')}: {r.get('event_type', r.get('purpose',''))}")
            if today_ev.empty:
                out.append("- none scheduled")
            out += ["", f"**This week: {len(week_ev)} events** (results/board meetings)", ""]
            self.facts.append(f"{len(today_ev)} corporate events today")
        else:
            out += ["Events: N/A", ""]

        n = _read("news")
        if n is not None:
            n = n.copy()
            score_col = next((c for c in ("sentiment_7d", "sentiment_score", "score")
                              if c in n.columns), None)
            head_col  = next((c for c in ("latest_headline", "headline", "title")
                              if c in n.columns), None)
            if score_col:
                n["_s"] = pd.to_numeric(n[score_col], errors="coerce")
                n = n.dropna(subset=["_s"])
                pos = n.nlargest(5, "_s")
                neg = n.nsmallest(3, "_s")
                out.append("**Stocks in news (positive sentiment):**")
                out += [f"- {r.get('symbol','')}: {str(r.get(head_col, ''))[:90]}"
                        for _, r in pos.iterrows()]
                out.append("**Stocks in news (negative sentiment):**")
                out += [f"- {r.get('symbol','')}: {str(r.get(head_col, ''))[:90]}"
                        for _, r in neg.iterrows()]
                out.append("")
            else:
                out += ["News: N/A -- unrecognised schema", ""]
        else:
            out += ["News: N/A", ""]

        d = _read("deals")
        if d is not None and "inst_net_value_cr" in d.columns:
            d["inst_net_value_cr"] = pd.to_numeric(d["inst_net_value_cr"], errors="coerce")
            top = d.nlargest(5, "inst_net_value_cr")
            out.append("**Top institutional deal flow (30D net):**")
            out += [f"- {r['symbol']}: {r['inst_net_value_cr']:.0f} cr" for _, r in top.iterrows()]
            out.append("")

        ins = _read("insider")
        if ins is not None:
            out.append(f"**Insider signals on file: {len(ins)}** (see insider_signals.csv)")
            out.append("")
        return out

    def _sec_scanner(self) -> list[str]:
        out = ["## 10. INSTITUTIONAL SCANNER & WATCHLISTS", ""]
        c = _read("conviction")
        if c is not None:
            high = c[c["tier"] == "HIGH"].head(10)
            out.append("**High-conviction buys (efficacy-weighted, liquidity-gated):**")
            out += [f"- {r['symbol']} ({r['sector']}) conv {r['conviction']} -- {r['supporting_evidence']}"
                    for _, r in high.iterrows()]
            out.append("")
            self.facts.append("top conviction: " + ", ".join(high["symbol"].head(5)))
        tc = _read("trade_conv")
        if tc is not None and "action" in tc.columns:
            swing = tc[tc["action"].isin(["STRONG_BUY", "BUY"])].nlargest(10, "score")
            out.append("**Swing candidates (trade conviction):**")
            out += [f"- {r['symbol']}: score {r['score']:.0f}, entry {r.get('entry_low')}-{r.get('entry_high')}, SL {r.get('stop_loss')}"
                    for _, r in swing.iterrows()]
            out.append("")
        t = _read("technical")
        if t is not None:
            t = t.copy()
            t["bb_squeeze_b"] = t.get("bb_squeeze").astype(str).str.lower().isin(["true", "1"])
            brk = t[t["bb_squeeze_b"] & t["trend_signal"].isin(["UPTREND", "STRONG_UPTREND"])].head(10)
            out.append("**Breakout setups (volatility squeeze in uptrend):**")
            out += [f"- {r['symbol']} (close {r['close_now']}, vs 52wH {r['prox_52w_high']}%)"
                    for _, r in brk.iterrows()]
            out.append("")
            rsi = pd.to_numeric(t.get("rsi"), errors="coerce")
            avoid = t[(t["trend_signal"] == "DOWNTREND") & (rsi < 40)].head(10)
            out.append("**Avoid (downtrend + weak momentum):**")
            out += [f"- {r['symbol']}" for _, r in avoid.iterrows()]
            out.append("")
        return out

    def _sec_risk(self) -> list[str]:
        out = ["## 11. RISK DASHBOARD (DATA-DRIVEN)", ""]
        risks = []
        v = self.bias.get("india_vix")
        if v is not None:
            risks.append(f"India VIX {v:.1f}: " + ("elevated -- expect wide swings" if v >= 17
                          else "moderate" if v >= 13 else "low -- stable regime"))
        if self.bias.get("regime") in ("DISTRIBUTION", "STRONG_DISTRIBUTION"):
            risks.append("Institutional regime is DISTRIBUTION -- rallies may be sold")
        g = self.bias.get("global_avg_chg", 0)
        if abs(g) >= 0.8:
            risks.append(f"Large overnight global move ({_fmt_chg(g)}) -- gap risk at open")
        if not risks:
            risks.append("No elevated data-driven risk flags this morning")
        out += [f"- {r}" for r in risks]
        out += ["", "Geopolitical/event risks are NOT auto-generated (no reliable free "
                "calendar feed) -- check RBI/Fed schedules manually.", ""]
        return out

    def _sec_plan(self) -> list[str]:
        bias = self._bias_label()
        out = ["## 12-14. TRADING PLAN", "",
               f"- Market bias: **{bias}**",
               f"- NIFTY expected range (option walls): **{self.bias.get('nifty_range', 'n/a')}**",
               f"- Trend context: {self.bias.get('nifty_trend', 'n/a')} | "
               f"A/D yesterday {self.bias.get('ad_ratio', 'n/a')} | PCR {self.bias.get('pcr', 'n/a')}",
               f"- Preferred sectors: {', '.join(self.bias.get('top_sectors', []) or ['n/a'])}",
               f"- Avoid sectors: {', '.join(self.bias.get('weak_sectors', []) or ['n/a'])}",
               f"- Strategy: {self._strategy_line(bias)}", ""]
        return out

    def _bias_label(self) -> str:
        score = 0.0
        g = self.bias.get("global_avg_chg", 0)
        score += max(min(g, 1.5), -1.5)
        ad = self.bias.get("ad_ratio")
        if ad: score += 0.5 if ad > 1.5 else (-0.5 if ad < 0.7 else 0)
        pcr = self.bias.get("pcr")
        try:
            pcr = float(pcr)
            score += 0.4 if pcr > 1.1 else (-0.4 if pcr < 0.7 else 0)
        except (TypeError, ValueError):
            pass
        regime = self.bias.get("regime", "")
        score += {"STRONG_ACCUMULATION": 0.8, "ACCUMULATION": 0.4,
                  "DISTRIBUTION": -0.4, "STRONG_DISTRIBUTION": -0.8}.get(regime, 0)
        self.bias["bias_score"] = round(score, 2)
        return ("BULLISH" if score >= 0.8 else "MILDLY BULLISH" if score >= 0.3
                else "BEARISH" if score <= -0.8 else "MILDLY BEARISH" if score <= -0.3
                else "NEUTRAL")

    @staticmethod
    def _strategy_line(bias: str) -> str:
        return {
            "BULLISH":        "buy on dips toward the put wall; avoid chasing gap-ups",
            "MILDLY BULLISH": "selective longs in preferred sectors; keep position sizes normal",
            "NEUTRAL":        "range trade between the option walls; no directional conviction",
            "MILDLY BEARISH": "reduce leverage; only high-conviction names; quick profits",
            "BEARISH":        "defensive -- protect capital, avoid fresh longs into strength",
        }.get(bias, "trade the levels, not the noise")

    # ── AI synthesis (data-locked) ────────────────────────────────────────────

    def _ai_synthesis(self) -> tuple[str, str]:
        bias = self._bias_label()
        fact_sheet = "\n".join(f"- {f}" for f in self.facts)
        fallback_exec = (
            f"Market bias: **{bias}** (score {self.bias.get('bias_score')}). "
            f"Regime {self.bias.get('regime', 'n/a')}, NIFTY range "
            f"{self.bias.get('nifty_range', 'n/a')}, preferred sectors "
            f"{', '.join(self.bias.get('top_sectors', []) or ['n/a'])}."
        )
        fallback_intel = (
            f"- Bias score: {self.bias.get('bias_score')} -> {bias}\n"
            f"- Regime: {self.bias.get('regime', 'n/a')} | India VIX: "
            f"{self.bias.get('india_vix', 'n/a')} | PCR: {self.bias.get('pcr', 'n/a')}\n"
            f"- (LLM synthesis unavailable -- deterministic summary shown)"
        )
        try:
            from engines.common.llm_client import call_llm
            prompt = (
                "You are the AI layer of a pre-market institutional brief for "
                "Indian equities. Using ONLY the facts below -- do not invent "
                "any number, event or name not present -- write:\n"
                "1) EXEC: a 5-line executive summary (bias, opening cue, key "
                "level(s), theme sectors, one-line strategy).\n"
                "2) INTEL: 8-10 bullet 'AI Market Intelligence' insights: "
                "read-through of institutional positioning, risk-on/off call, "
                "trend-day vs range-day probability (qualitative, from breadth "
                "+ PCR + VIX), confidence meter GREEN/YELLOW/RED, and an "
                "overall stance (Aggressive Buy / Buy on Dips / Neutral / "
                "Defensive / Sell into Strength).\n"
                f"Deterministic bias already computed: {bias}.\n"
                "Separate the two parts with the line ===INTEL===\n\n"
                f"FACTS:\n{fact_sheet}"
            )
            resp = call_llm(system="You write terse, data-locked institutional briefs.",
                            user=prompt, max_tokens=900, temperature=0.2)
            if resp and "===INTEL===" in resp:
                exec_part, intel_part = resp.split("===INTEL===", 1)
                return exec_part.strip(), intel_part.strip()
            if resp:
                return fallback_exec, resp.strip()
        except Exception as e:
            logger.warning("[DMB] AI synthesis failed: %s", e)
        return fallback_exec, fallback_intel

    # ── Delivery ──────────────────────────────────────────────────────────────

    def _deliver(self, report_path: Path, exec_summary: str) -> None:
        try:
            from alerts.telegram_bot import send_raw, send_document
            digest = (
                f"DAILY MARKET BRIEF -- {self.today.strftime('%d %b %Y')}\n"
                f"{'-' * 32}\n{exec_summary}\n\n"
                f"NIFTY range: {self.bias.get('nifty_range', 'n/a')} | "
                f"PCR {self.bias.get('pcr', 'n/a')} | "
                f"VIX {self.bias.get('india_vix', 'n/a')}\n"
                f"Full report attached."
            )
            send_raw(digest)
            send_document(report_path, caption=f"DMB {self.today.isoformat()}")
            logger.info("[DMB] Delivered to Telegram")
        except Exception as e:
            logger.warning("[DMB] Telegram delivery failed (report still saved): %s", e)


def run_full_briefing(deliver: bool = True) -> bool:
    """08:45 entry point: refresh the three feeders, then assemble + deliver."""
    from engines.briefing.global_snapshot_engine import GlobalSnapshotEngine
    from engines.briefing.market_breadth_engine import MarketBreadthEngine
    from engines.briefing.index_options_engine import IndexOptionsEngine
    for eng in (GlobalSnapshotEngine, MarketBreadthEngine, IndexOptionsEngine):
        try:
            eng().run()
        except Exception as e:
            logger.error("[DMB] Feeder %s failed: %s -- continuing", eng.__name__, e)
    return DMBEngine().run(deliver=deliver)


if __name__ == "__main__":
    deliver = "--no-telegram" not in sys.argv
    sys.exit(0 if run_full_briefing(deliver=deliver) else 1)
