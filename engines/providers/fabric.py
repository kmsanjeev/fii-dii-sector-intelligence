"""Capability-aware, read-only provider metadata and resolution.

This module deliberately does not own credentials or make network calls.  FII's
existing broker adapters remain the execution boundary for local portfolio
sync, while this fabric answers the safe question: which configured provider
could satisfy a requested market-data capability?
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable


class ProviderType(StrEnum):
    LOCAL_GOVERNED = "LOCAL_GOVERNED"
    BROKER = "BROKER"
    LICENSED_MARKET_DATA = "LICENSED_MARKET_DATA"
    PUBLIC_COMPATIBILITY = "PUBLIC_COMPATIBILITY"
    FILE_IMPORT = "FILE_IMPORT"
    RESEARCH_CANDIDATE = "RESEARCH_CANDIDATE"


class Capability(StrEnum):
    EOD_EQUITY_HISTORY = "EOD_EQUITY_HISTORY"
    EOD_FNO_HISTORY = "EOD_FNO_HISTORY"
    INTRADAY_HISTORY = "INTRADAY_HISTORY"
    LIVE_LTP = "LIVE_LTP"
    LIVE_QUOTE = "LIVE_QUOTE"
    LIVE_WEBSOCKET = "LIVE_WEBSOCKET"
    MARKET_DEPTH = "MARKET_DEPTH"
    FUTURES_OI = "FUTURES_OI"
    OPTION_CHAIN = "OPTION_CHAIN"
    OPTION_GREEKS_SOURCE = "OPTION_GREEKS_SOURCE"
    HOLDINGS = "HOLDINGS"
    POSITIONS = "POSITIONS"
    FUNDS = "FUNDS"
    TRADES = "TRADES"
    ORDER_HISTORY = "ORDER_HISTORY"
    PORTFOLIO_IMPORT = "PORTFOLIO_IMPORT"
    ORDER_PREPARE = "ORDER_PREPARE"
    ORDER_EXECUTE = "ORDER_EXECUTE"


@dataclass(frozen=True)
class ProviderManifest:
    provider_id: str
    display_name: str
    provider_type: ProviderType
    source_authority: str
    capabilities: frozenset[Capability] = frozenset()
    auth_modes: tuple[str, ...] = ()
    account_required: bool = False
    data_entitlement_required: bool = False
    licensing_state: str = "UNREVIEWED"
    supported_segments: tuple[str, ...] = ()
    supported_intervals: tuple[str, ...] = ()
    live_support: bool = False
    historical_support: bool = False
    portfolio_support: bool = False
    execution_support: bool = False
    rate_limits: str = "NOT_RECORDED"
    health_probe: str = "NOT_CONFIGURED"
    adapter_version: str = "0.1.0"
    documentation_url: str = ""
    limitations: tuple[str, ...] = ()
    capability_states: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ProviderConnection:
    connection_id: str
    provider_id: str
    scope: str = "workspace"
    display_name: str = ""
    auth_state: str = "NOT_CONFIGURED"
    connection_state: str = "DISCONNECTED"
    credential_reference: str = ""
    authorized_capabilities: frozenset[Capability] = frozenset()
    entitlement_state: str = "UNKNOWN"
    connected_at: str | None = None
    last_validated_at: str | None = None
    expires_at: str | None = None
    last_success_at: str | None = None
    last_failure: str | None = None
    health: str = "UNKNOWN"
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class Resolution:
    capability: Capability
    selected_provider: str | None
    provider_type: ProviderType | None
    reason: str
    source_authority: str | None
    connection_id: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    freshness_expectation: str = "UNSPECIFIED"
    limitations: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()


class ProviderFabric:
    """Deterministic registry and capability resolver; no secret access."""

    def __init__(self, manifests: Iterable[ProviderManifest] = (), connections: Iterable[ProviderConnection] = ()) -> None:
        self._manifests = {item.provider_id: item for item in manifests}
        self._connections = {item.connection_id: item for item in connections}

    def register_manifest(self, manifest: ProviderManifest) -> None:
        if manifest.provider_id in self._manifests:
            raise ValueError(f"provider already registered: {manifest.provider_id}")
        self._manifests[manifest.provider_id] = manifest

    def upsert_connection(self, connection: ProviderConnection) -> None:
        if connection.provider_id not in self._manifests:
            raise ValueError(f"provider not registered: {connection.provider_id}")
        self._connections[connection.connection_id] = connection

    def manifests(self) -> tuple[ProviderManifest, ...]:
        return tuple(self._manifests[key] for key in sorted(self._manifests))

    def connections(self) -> tuple[ProviderConnection, ...]:
        return tuple(self._connections[key] for key in sorted(self._connections))

    def resolve(self, capability: Capability, *, allow_research: bool = False) -> Resolution:
        candidates: list[tuple[int, ProviderManifest, ProviderConnection | None]] = []
        for manifest in self._manifests.values():
            if capability not in manifest.capabilities:
                continue
            if manifest.provider_type == ProviderType.RESEARCH_CANDIDATE and not allow_research:
                continue
            matching = [c for c in self._connections.values() if c.provider_id == manifest.provider_id]
            if manifest.provider_type == ProviderType.BROKER and not matching:
                continue
            if manifest.account_required and not matching:
                continue
            for connection in matching or [None]:
                if connection and connection.connection_state not in {"CONNECTED", "AVAILABLE"}:
                    continue
                if connection and capability not in connection.authorized_capabilities:
                    continue
                if connection and connection.entitlement_state not in {"ENTITLED", "NOT_REQUIRED"}:
                    continue
                if connection and connection.health not in {"HEALTHY", "AVAILABLE"}:
                    continue
                score = 0
                score += 40 if manifest.provider_type == ProviderType.LOCAL_GOVERNED else 30
                score += 20 if manifest.provider_type == ProviderType.BROKER else 0
                score += 10 if manifest.licensing_state in {"INTERNAL", "REVIEWED"} else 0
                candidates.append((score, manifest, connection))
        candidates.sort(key=lambda item: (-item[0], item[1].provider_id))
        if not candidates:
            live = capability in {
                Capability.INTRADAY_HISTORY,
                Capability.LIVE_LTP,
                Capability.LIVE_QUOTE,
                Capability.LIVE_WEBSOCKET,
                Capability.MARKET_DEPTH,
                Capability.FUTURES_OI,
                Capability.OPTION_CHAIN,
                Capability.OPTION_GREEKS_SOURCE,
            }
            return Resolution(
                capability=capability,
                selected_provider=None,
                provider_type=None,
                reason="AUTHORIZED_LIVE_PROVIDER_REQUIRED" if live else "NO_CONFIGURED_PROVIDER",
                source_authority=None,
                limitations=("No provider satisfied capability, authentication, entitlement and health policy.",),
            )
        _, selected, connection = candidates[0]
        return Resolution(
            capability=capability,
            selected_provider=selected.provider_id,
            provider_type=selected.provider_type,
            reason="capability_and_connection_policy_match",
            source_authority=selected.source_authority,
            connection_id=connection.connection_id if connection else None,
            freshness_expectation="LIVE" if capability in {Capability.LIVE_LTP, Capability.LIVE_QUOTE, Capability.LIVE_WEBSOCKET, Capability.MARKET_DEPTH} else "EOD_OR_PROVIDER_DEFINED",
            limitations=selected.limitations + (connection.limitations if connection else ()),
            alternatives=tuple(item[1].provider_id for item in candidates[1:]),
        )


def default_provider_fabric() -> ProviderFabric:
    """Return policy metadata for the current FII providers."""
    local = frozenset({Capability.EOD_EQUITY_HISTORY, Capability.EOD_FNO_HISTORY, Capability.PORTFOLIO_IMPORT})
    dhan_market = frozenset({Capability.INTRADAY_HISTORY, Capability.LIVE_LTP, Capability.LIVE_QUOTE, Capability.LIVE_WEBSOCKET, Capability.MARKET_DEPTH, Capability.FUTURES_OI, Capability.OPTION_CHAIN, Capability.OPTION_GREEKS_SOURCE})
    dhan_portfolio = frozenset({Capability.HOLDINGS, Capability.POSITIONS, Capability.FUNDS, Capability.TRADES, Capability.ORDER_HISTORY})
    zerodha_market = frozenset({Capability.INTRADAY_HISTORY, Capability.LIVE_LTP, Capability.LIVE_QUOTE, Capability.LIVE_WEBSOCKET, Capability.MARKET_DEPTH, Capability.FUTURES_OI})
    zerodha_portfolio = frozenset({Capability.HOLDINGS, Capability.POSITIONS, Capability.FUNDS, Capability.TRADES, Capability.ORDER_HISTORY})
    fabric = ProviderFabric([
        ProviderManifest("local-governed", "FII governed local stores", ProviderType.LOCAL_GOVERNED, "FII-DII-Sector-Intelligence", local, historical_support=True, licensing_state="INTERNAL", health_probe="local-files", limitations=("No live market data.",)),
        ProviderManifest("dhan", "DhanHQ", ProviderType.BROKER, "DhanHQ API", dhan_market | dhan_portfolio, ("TOTP_ACCESS_TOKEN", "ACCESS_TOKEN", "API_KEY_OAUTH"), True, True, "PROVIDER_REVIEWED", ("NSE", "BSE", "NFO", "BFO"), ("1", "5", "15", "25", "60"), True, True, True, False, "provider-defined", "authenticated API health probe", "2.2.0", "https://dhanhq.co/docs/v2/", ("Data API entitlement may be required.", "Execution is intentionally disabled by FII."), (("INTRADAY_HISTORY", "DOCUMENTED_UNVALIDATED"), ("LIVE_LTP", "DOCUMENTED_UNVALIDATED"), ("LIVE_QUOTE", "DOCUMENTED_UNVALIDATED"), ("LIVE_WEBSOCKET", "DOCUMENTED_UNVALIDATED"), ("MARKET_DEPTH", "DOCUMENTED_UNVALIDATED"), ("FUTURES_OI", "DOCUMENTED_UNVALIDATED"), ("OPTION_CHAIN", "DOCUMENTED_UNVALIDATED"), ("OPTION_GREEKS_SOURCE", "DOCUMENTED_UNVALIDATED"))),
        ProviderManifest("zerodha-kite", "Zerodha Kite Connect", ProviderType.BROKER, "Kite Connect API", zerodha_market | zerodha_portfolio, ("REDIRECT_REQUEST_TOKEN",), True, True, "PROVIDER_REVIEWED", ("NSE", "BSE", "NFO", "BFO", "MCX"), ("minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"), True, True, True, False, "provider-defined", "authenticated API health probe", "unvalidated", "https://kite.trade/docs/connect/v3/", ("Official docs reviewed for candles, quotes and WebSocket; option-chain/Greeks API not identified.", "Execution is intentionally disabled by FII."), (("INTRADAY_HISTORY", "DOCUMENTED_UNVALIDATED"), ("LIVE_LTP", "DOCUMENTED_UNVALIDATED"), ("LIVE_QUOTE", "DOCUMENTED_UNVALIDATED"), ("LIVE_WEBSOCKET", "DOCUMENTED_UNVALIDATED"), ("MARKET_DEPTH", "DOCUMENTED_UNVALIDATED"), ("FUTURES_OI", "DOCUMENTED_UNVALIDATED"))),
        ProviderManifest("hdfc-sky", "HDFC Sky Open API", ProviderType.BROKER, "HDFC Sky developer portal", frozenset(), ("REDIRECT_REQUEST_TOKEN",), True, True, "POLICY_REVIEW_REQUIRED", ("NSE", "BSE", "NFO"), (), False, False, False, False, "UNVERIFIED", "not configured", "unvalidated", "https://developer.hdfcsky.com/", ("Current official API scope and entitlement require validation before any capability is advertised.",)),
        ProviderManifest("csv-import", "Broker CSV import", ProviderType.FILE_IMPORT, "User-provided broker export", frozenset({Capability.PORTFOLIO_IMPORT}), licensing_state="USER_PROVIDED", portfolio_support=True, health_probe="file-presence", limitations=("Snapshot import only; no live or historical market feed.",)),
        ProviderManifest("yfinance", "yfinance compatibility", ProviderType.PUBLIC_COMPATIBILITY, "Yahoo Finance compatibility layer", frozenset({Capability.EOD_EQUITY_HISTORY}), historical_support=True, licensing_state="LOCAL_RESEARCH", health_probe="optional", limitations=("Not production authority; terms and availability require policy review.",)),
        ProviderManifest("nselib", "nselib compatibility", ProviderType.RESEARCH_CANDIDATE, "Community package", frozenset({Capability.EOD_EQUITY_HISTORY, Capability.EOD_FNO_HISTORY}), historical_support=True, licensing_state="POLICY_REVIEW_REQUIRED", health_probe="optional", limitations=("Research candidate; do not use as production authority without review.",)),
        ProviderManifest("nsepython", "nsepython compatibility", ProviderType.RESEARCH_CANDIDATE, "Community package", frozenset({Capability.EOD_EQUITY_HISTORY, Capability.EOD_FNO_HISTORY, Capability.INTRADAY_HISTORY}), historical_support=True, licensing_state="POLICY_REVIEW_REQUIRED", health_probe="optional", limitations=("Research candidate; do not use as production authority without review.",)),
    ])
    return fabric
