from engines.providers.fabric import Capability, ProviderConnection, ProviderType, default_provider_fabric


def test_no_broker_preserves_local_eod_resolution() -> None:
    fabric = default_provider_fabric()
    result = fabric.resolve(Capability.EOD_EQUITY_HISTORY)
    assert result.selected_provider == "local-governed"
    assert result.provider_type == ProviderType.LOCAL_GOVERNED
    assert result.connection_id is None


def test_live_capability_fails_closed_without_connected_provider() -> None:
    result = default_provider_fabric().resolve(Capability.LIVE_QUOTE)
    assert result.selected_provider is None
    assert result.reason == "AUTHORIZED_LIVE_PROVIDER_REQUIRED"


def test_connected_broker_can_resolve_intraday_without_exposing_secrets() -> None:
    fabric = default_provider_fabric()
    fabric.upsert_connection(ProviderConnection(
        connection_id="test-dhan",
        provider_id="dhan",
        connection_state="CONNECTED",
        auth_state="CONFIGURED",
        entitlement_state="ENTITLED",
        authorized_capabilities=frozenset({Capability.INTRADAY_HISTORY}),
        credential_reference="local-encrypted-broker-auth",
        health="HEALTHY",
    ))
    result = fabric.resolve(Capability.INTRADAY_HISTORY)
    assert result.selected_provider == "dhan"
    assert result.connection_id == "test-dhan"
    assert "access_token" not in str(result)


def test_research_candidates_are_not_selected_by_default() -> None:
    result = default_provider_fabric().resolve(Capability.EOD_FNO_HISTORY)
    assert result.selected_provider == "local-governed"
    assert result.provider_type != ProviderType.RESEARCH_CANDIDATE
