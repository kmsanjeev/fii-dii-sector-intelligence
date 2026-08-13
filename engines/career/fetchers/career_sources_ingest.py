from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from engines.common import config as cfg


@dataclass(frozen=True)
class CareerSourceBundle:
    signals: pd.DataFrame
    classification: pd.DataFrame
    chart_index: dict[str, dict[str, Any]]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_signals() -> pd.DataFrame:
    path = cfg.INTELLIGENCE_DIR / "kundli_signals.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing kundli signals file: {path}")
    df = pd.read_csv(path)
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


@lru_cache(maxsize=1)
def load_classification() -> pd.DataFrame:
    path = cfg.REFERENCE_DIR / "company_classification_v4.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing company classification file: {path}")
    df = pd.read_csv(path)
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


@lru_cache(maxsize=1)
def load_chart_index() -> dict[str, dict[str, Any]]:
    chart_dir = cfg.INTELLIGENCE_DIR / "kundli"
    if not chart_dir.exists():
        raise FileNotFoundError(f"Missing kundli chart directory: {chart_dir}")
    index: dict[str, dict[str, Any]] = {}
    for path in chart_dir.glob("*_kundli.json"):
        symbol = path.stem.replace("_kundli", "").upper()
        try:
            index[symbol] = _read_json(path)
        except Exception:
            index[symbol] = {}
    return index


def load_bundle() -> CareerSourceBundle:
    return CareerSourceBundle(
        signals=load_signals().copy(),
        classification=load_classification().copy(),
        chart_index=dict(load_chart_index()),
    )

