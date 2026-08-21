from __future__ import annotations

from backend.services import governed_theme_intelligence as service


def test_registry_is_bounded_and_stable() -> None:
    registry = service.registry()
    assert registry["schema_version"] == "theme-registry-1.0"
    assert len(registry["themes"]) == 15
    assert len({item["theme_id"] for item in registry["themes"]}) == 15
    assert all(item["aliases"] for item in registry["themes"])


def test_membership_is_many_to_many_and_evidence_bounded() -> None:
    memberships = service.memberships_for()
    assert memberships
    assert {item["source"] for item in memberships} <= {"classification_v4", "cross_theme"}
    assert all(item["status"] == "ACTIVE" for item in memberships)
    per_symbol: dict[str, set[str]] = {}
    for item in memberships:
        per_symbol.setdefault(item["symbol"], set()).add(item["theme_id"])
    assert any(len(theme_ids) > 1 for theme_ids in per_symbol.values())
    assert all(item["evidence"] and item["method"] for item in memberships)


def test_theme_intelligence_preserves_missing_data_and_context_boundaries() -> None:
    detail = service.intelligence("theme.capex-cycle")
    assert detail["contract_version"] == "theme-intelligence-1.0"
    assert set(detail["performance"]["windows"]) == {"1D", "3D", "5D", "10D", "20D"}
    assert detail["institutional_context"]["scope"] == "MARKET_LEVEL_CONTEXT_ONLY"
    assert detail["institutional_context"]["theme_attribution"] == "NO_THEME_INSTITUTIONAL_ATTRIBUTION"
    assert detail["cross_layer_context"]["stock"] == "REUSES_PROVIDER_STOCK_DATA; NO_NEW_STOCK_SCORE"
    assert detail["membership"]["historical_snapshots"] == "NOT_AVAILABLE"


def test_summary_matches_veda_provider_data_status_contract() -> None:
    payload = service.summary()
    assert payload["contract_version"] == "theme-intelligence-1.0"
    assert payload["count"] == 15
    assert payload["data_status"]["last_successful_update"] == "2026-06-30"
    assert len(payload["themes"]) == payload["count"]


def test_stock_memberships_are_current_read_only_records() -> None:
    memberships = service.memberships_for(symbol="AARTIIND")
    assert memberships
    assert all(item["symbol"] == "AARTIIND" for item in memberships)
    assert any(item["relationship_type"] == "PRIMARY" for item in memberships)
    assert any(item["relationship_type"] == "CROSS_THEME" for item in memberships)


def test_valid_runtime_artifacts_load_without_rebuilding_or_reading_prices(
    monkeypatch,
) -> None:
    service.build_runtime_cache()
    service.reset_cache()

    def unexpected_membership_build(_registry):
        raise AssertionError("valid membership snapshot was rebuilt")

    def unexpected_price_read(*_args, **_kwargs):
        raise AssertionError("valid price projection performed a Parquet read")

    monkeypatch.setattr(service, "_build_memberships", unexpected_membership_build)
    monkeypatch.setattr(service.pd, "read_parquet", unexpected_price_read)
    payload = service.summary()
    assert payload["count"] == 15


def test_price_manifest_change_invalidates_projection(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        service, "PRICE_PROJECTION_PATH", tmp_path / "price_projection.json"
    )
    service.build_runtime_cache()
    service.reset_cache()
    original_state = service._file_state
    changed_state = service.PRICE_MANIFEST_PATH.stat()

    def changed_file_state(path):
        state = original_state(path)
        if path == service.PRICE_MANIFEST_PATH and state is not None:
            return (state[0] + 1, state[1])
        return state

    calls = []

    def bounded_fake_price(symbol):
        calls.append(symbol)
        return {window: 0.0 for window in service.WINDOWS} | {"as_of": "2026-08-20"}

    monkeypatch.setattr(service, "_file_state", changed_file_state)
    monkeypatch.setattr(service, "_stock_returns", bounded_fake_price)
    service.intelligence("theme.psu-revival")
    assert calls
    assert changed_state.st_size == service.PRICE_MANIFEST_PATH.stat().st_size
    service.reset_cache()
