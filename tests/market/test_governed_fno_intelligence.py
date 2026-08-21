from __future__ import annotations

import pandas as pd

from backend.services.governed_fno_intelligence import (
    build_governed_fno_intelligence,
    normalize_fno_frame,
)


def _current_rows(trade_date: str, expiry: str = "2026-08-25", *, oi: int = 100, price: float = 101.0):
    return pd.DataFrame(
        [
            {
                "TradDt": trade_date,
                "FinInstrmTp": "STF",
                "FinInstrmId": f"F-{trade_date}",
                "TckrSymb": "ABC",
                "XpryDt": expiry,
                "StrkPric": 0,
                "OptnTp": "XX",
                "ClsPric": price,
                "UndrlygPric": 100,
                "OpnIntrst": oi,
                "ChngInOpnIntrst": 10,
                "TtlTradgVol": 50,
                "TtlTrfVal": 5000,
            },
            {
                "TradDt": trade_date,
                "FinInstrmTp": "STO",
                "FinInstrmId": f"C-{trade_date}",
                "TckrSymb": "ABC",
                "XpryDt": expiry,
                "StrkPric": 100,
                "OptnTp": "CE",
                "ClsPric": 2,
                "OpnIntrst": 1000,
                "ChngInOpnIntrst": 5,
                "TtlTradgVol": 20,
                "TtlTrfVal": 200,
            },
            {
                "TradDt": trade_date,
                "FinInstrmTp": "STO",
                "FinInstrmId": f"P-{trade_date}",
                "TckrSymb": "ABC",
                "XpryDt": expiry,
                "StrkPric": 100,
                "OptnTp": "PE",
                "ClsPric": 2,
                "OpnIntrst": 2000,
                "ChngInOpnIntrst": 7,
                "TtlTradgVol": 30,
                "TtlTrfVal": 300,
            },
            {
                "TradDt": trade_date,
                "FinInstrmTp": "IDO",
                "FinInstrmId": f"IC-{trade_date}",
                "TckrSymb": "NIFTY",
                "XpryDt": expiry,
                "StrkPric": 20000,
                "OptnTp": "CE",
                "ClsPric": 2,
                "OpnIntrst": 100,
                "ChngInOpnIntrst": 1,
                "TtlTradgVol": 10,
                "TtlTrfVal": 100,
            },
            {
                "TradDt": trade_date,
                "FinInstrmTp": "IDO",
                "FinInstrmId": f"IP-{trade_date}",
                "TckrSymb": "NIFTY",
                "XpryDt": expiry,
                "StrkPric": 20000,
                "OptnTp": "PE",
                "ClsPric": 2,
                "OpnIntrst": 50,
                "ChngInOpnIntrst": 1,
                "TtlTradgVol": 8,
                "TtlTrfVal": 80,
            },
        ]
    )


def test_legacy_schema_is_normalized_without_loss_of_instrument_class() -> None:
    frame = normalize_fno_frame(
        pd.DataFrame(
            [{
                "INSTRUMENT": "FUTIDX",
                "SYMBOL": "NIFTY",
                "EXPIRY_DT": "29-Jun-2000",
                "STRIKE_PR": 0,
                "OPTION_TYP": "XX",
                "CLOSE": 100,
                "OPEN_INT": 20,
                "CHG_IN_OI": 3,
                "CONTRACTS": 2,
                "VAL_INLAKH": 1,
                "TIMESTAMP": "12-Jun-2000",
            }]
        )
    )
    assert frame.iloc[0]["instrument_class"] == "FUTURE"
    assert frame.iloc[0]["underlying_type"] == "INDEX"
    assert frame.iloc[0]["expiry_date"] == "2000-06-29"
    assert frame.iloc[0]["underlying_id"] == "INDEX:NIFTY"


def test_nearest_expiry_is_not_highest_oi(tmp_path) -> None:
    older = _current_rows("2026-08-17", oi=90, price=99)
    latest = _current_rows("2026-08-19", oi=100, price=101)
    later_expiry = latest.iloc[[0]].copy()
    later_expiry["XpryDt"] = "2026-09-29"
    later_expiry["FinInstrmId"] = "F-LATER"
    later_expiry["OpnIntrst"] = 999999
    latest = pd.concat([latest, later_expiry], ignore_index=True)
    older.to_csv(tmp_path / "fo_20260817.csv", index=False)
    latest.to_csv(tmp_path / "fo_20260819.csv", index=False)

    result = build_governed_fno_intelligence(fno_dir=tmp_path, lookback=2)
    record = next(item for item in result["futures"] if item["symbol"] == "ABC")
    assert record["expiry"] == "2026-08-25"
    assert record["contract_id"] == "F-2026-08-19"


def test_roll_transition_suppresses_cross_expiry_price_signal(tmp_path) -> None:
    previous = _current_rows("2026-08-18", expiry="2026-08-25", oi=100, price=100)
    latest = _current_rows("2026-08-19", expiry="2026-09-29", oi=140, price=120)
    previous.to_csv(tmp_path / "fo_20260818.csv", index=False)
    latest.to_csv(tmp_path / "fo_20260819.csv", index=False)

    result = build_governed_fno_intelligence(fno_dir=tmp_path, lookback=2)
    record = next(item for item in result["futures"] if item["symbol"] == "ABC")
    assert record["roll_detected"] is True
    assert record["oi_signal"] == "ROLL_TRANSITION"
    assert record["price_change_1d"] is None


def test_pcr_is_scoped_and_not_directional(tmp_path) -> None:
    frame = _current_rows("2026-08-19")
    frame.to_csv(tmp_path / "fo_20260819.csv", index=False)
    result = build_governed_fno_intelligence(fno_dir=tmp_path, lookback=1)
    assert result["pcr"]["scope"] == "ALL_ACTIVE_EXPIRIES"
    assert result["pcr"]["stock_options_oi"]["pcr_oi"] == 2.0
    assert result["pcr"]["index_options_oi"]["pcr_oi"] == 0.5
    assert result["pcr"]["signal"] == "UNINTERPRETED_DESCRIPTIVE_ONLY"
