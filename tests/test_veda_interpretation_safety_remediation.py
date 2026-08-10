import asyncio
import json
from pathlib import Path

from backend.routers.kundli import stock_kundli
from engines.ai.chatbot.tools.data_tools import get_astro_signal
from engines.ai.chatbot.tools.kundli_calculator import compute_personal_kundli


ROOT = Path(__file__).resolve().parents[1]
RISK_REGISTRY_PATH = ROOT / "docs" / "current-state" / "p005-r1" / "p005-r1_high_stakes_risk_register.json"

PERSONAL_FIXTURE = {
    "date_of_birth": "1984-11-03",
    "time_of_birth": "06:30",
    "place_name": "Mumbai",
    "latitude": 19.076,
    "longitude": 72.8777,
    "timezone_offset_hours": 5.5,
}


def _load_registry() -> list[dict]:
    with open(RISK_REGISTRY_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def test_stock_kundli_route_returns_bounded_finance_labels():
    payload = asyncio.run(
        stock_kundli(
            symbol="RELIANCE",
            include_gann=False,
            generate_narrative=False,
        )
    )

    chart = payload["kundli"]
    interpretation = payload["interpretation"]

    assert chart["astro_action"] == "Positive natal astrology signal"
    assert chart["astro_action_code"] == "BUY"
    assert chart["boundary_note"] == "Astrology-derived market heuristic only; not validated financial advice."

    assert interpretation["signal"] == "Strong positive astrology heuristic"
    assert interpretation["signal_code"] == "STRONG_BUY"
    assert interpretation["evidence_class"] == "ASTROLOGY_HEURISTIC"
    assert interpretation["source_status"] == "LEGACY_UNSOURCED"
    assert interpretation["high_stakes"] is True


def test_astrofinance_tool_returns_bounded_heuristic_payloads():
    banking = get_astro_signal("BANKING")
    assert banking["astro_action"] not in {"BUY", "HOLD", "CAUTION", "EXIT", "AVOID"}
    assert banking["astro_action_code"] in {"BUY", "HOLD", "CAUTION", "EXIT", "AVOID"}
    assert banking["evidence_class"] == "INTERNAL_HEURISTIC"
    assert banking["source_status"] == "UNVERIFIED"
    assert banking["boundary_note"] == "AstroFinance heuristic only; cross-check with market, technical, and fundamental evidence."
    assert "trading instruction" not in banking["astro_reason"].lower()

    ranking = get_astro_signal()
    assert ranking["all_sectors"]
    first = ranking["all_sectors"][0]
    assert first["astro_action"] not in {"BUY", "HOLD", "CAUTION", "EXIT", "AVOID"}
    assert first["astro_action_code"] in {"BUY", "HOLD", "CAUTION", "EXIT", "AVOID"}
    assert first["high_stakes"] is True


def test_personal_longevity_report_is_bounded_and_non_deterministic():
    payload = compute_personal_kundli(**PERSONAL_FIXTURE)
    report = payload["formatted_report"]

    assert "LONGEVITY & LIFE SPAN (AYURDAYA PRINCIPLES)" in report
    assert "Traditional Ayurdaya indicators are interpretive only." in report
    assert "not a factual lifespan or death prediction" in report
    assert "determine life span" not in report
    assert "supports long life" not in report
    assert "generally longer life span" not in report


def test_p005_r1_risk_registry_marks_all_p0_findings_mitigated():
    rows = {row["RISK_ID"]: row for row in _load_registry()}

    assert set(rows) == {
        "VEDA-P005-R1-RISK-0001",
        "VEDA-P005-R1-RISK-0002",
        "VEDA-P005-R1-RISK-0003",
        "VEDA-P005-R1-RISK-0004",
        "VEDA-P005-R1-RISK-0005",
    }
    assert rows["VEDA-P005-R1-RISK-0001"]["STATUS"] == "MITIGATED"
    assert rows["VEDA-P005-R1-RISK-0002"]["STATUS"] == "MITIGATED"
    assert rows["VEDA-P005-R1-RISK-0003"]["STATUS"] == "MITIGATED"
    assert rows["VEDA-P005-R1-RISK-0004"]["STATUS"] == "DEFERRED"
    assert rows["VEDA-P005-R1-RISK-0005"]["STATUS"] == "DEFERRED"
