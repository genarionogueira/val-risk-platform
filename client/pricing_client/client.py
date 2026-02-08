"""Pricing API client using sgqlc."""

from __future__ import annotations

import sys
from typing import Any

from sgqlc.endpoint.http import HTTPEndpoint

from pricing_client.marketdata import MarketdataClient
from pricing_client.types import (
    CDSInput,
    CurveInput,
    FXForwardInput,
    FixedFloatSwapInput,
    HazardCurveInput,
    MarketInput,
    MortgageInput,
    PricingResult,
    ZeroCouponBondInput,
    curve_snapshot_to_curve_input,
)


def _curve_to_vars(c: CurveInput) -> dict[str, Any]:
    """Serialize CurveInput to GraphQL variables (camelCase)."""
    return {
        "name": c.name,
        "pillars": c.pillars,
        "zeroRatesCc": c.zero_rates_cc,
        "t0": c.t0,
    }


def _hazard_curve_to_vars(h: HazardCurveInput) -> dict[str, Any]:
    """Serialize HazardCurveInput to GraphQL variables (camelCase)."""
    return {
        "name": h.name,
        "pillars": h.pillars,
        "hazardRates": h.hazard_rates,
        "t0": h.t0,
    }


def _market_to_vars(m: MarketInput) -> dict[str, Any]:
    """Serialize MarketInput to GraphQL variables (camelCase)."""
    result: dict[str, Any] = {
        "curves": [_curve_to_vars(c) for c in m.curves],
    }
    if m.hazard_curves:
        result["hazardCurves"] = [_hazard_curve_to_vars(h) for h in m.hazard_curves]
    if m.fx_spot:
        result["fxSpot"] = [{"pair": fx.pair, "spot": fx.spot} for fx in m.fx_spot]
    return result


def _bond_to_vars(b: ZeroCouponBondInput) -> dict[str, Any]:
    """Serialize ZeroCouponBondInput to GraphQL variables."""
    return {
        "curve": b.curve,
        "maturity": b.maturity,
        "notional": b.notional,
    }


def _fx_forward_to_vars(f: FXForwardInput) -> dict[str, Any]:
    """Serialize FXForwardInput to GraphQL variables (camelCase)."""
    return {
        "pair": f.pair,
        "baseCurve": f.base_curve,
        "quoteCurve": f.quote_curve,
        "maturity": f.maturity,
        "notionalBase": f.notional_base,
        "strike": f.strike,
    }


def _swap_to_vars(s: FixedFloatSwapInput) -> dict[str, Any]:
    """Serialize FixedFloatSwapInput to GraphQL variables (camelCase)."""
    return {
        "curve": s.curve,
        "notional": s.notional,
        "fixedRate": s.fixed_rate,
        "payTimes": s.pay_times,
        "t0": s.t0,
    }


def _mortgage_to_vars(m: MortgageInput) -> dict[str, Any]:
    """Serialize MortgageInput to GraphQL variables (camelCase)."""
    return {
        "curve": m.curve,
        "notional": m.notional,
        "annualRate": m.annual_rate,
        "termYears": m.term_years,
        "paymentsPerYear": m.payments_per_year,
    }


def _cds_to_vars(c: CDSInput) -> dict[str, Any]:
    """Serialize CDSInput to GraphQL variables (camelCase)."""
    return {
        "discountCurve": c.discount_curve,
        "survivalCurve": c.survival_curve,
        "notional": c.notional,
        "premiumRate": c.premium_rate,
        "payTimes": c.pay_times,
        "recovery": c.recovery,
        "t0": c.t0,
        "protectionBuyer": c.protection_buyer,
    }


def _is_jupyter() -> bool:
    """True if running inside Jupyter (IPython kernel)."""
    if "IPython" not in sys.modules:
        return False
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and getattr(ip, "kernel", None) is not None
    except Exception:
        return False


def _tick_display(
    header: str,
    line: str,
    is_first: bool,
    use_jupyter: bool,
) -> None:
    """Refresh display in place: Jupyter clear_output or terminal \\r."""
    if use_jupyter:
        try:
            from IPython.display import clear_output
            clear_output(wait=True)
            print(header)
            print(line)
        except Exception:
            print(header if is_first else "")
            print(f"\r{line}", end="", flush=True)
    else:
        if is_first:
            print(header)
        # Pad line so shorter updates don't leave leftover chars
        padded = line.ljust(80)
        print(f"\r{padded}", end="", flush=True)


def _tick_display_rows(
    row1: str,
    row2: str,
    is_first: bool,
    use_jupyter: bool,
) -> None:
    """Refresh two-row display in place: Jupyter clear_output or terminal reprint."""
    if use_jupyter:
        try:
            from IPython.display import clear_output
            clear_output(wait=True)
            print(row1)
            print(row2)
        except Exception:
            if is_first:
                print(row1)
            print(row2)
    else:
        if is_first:
            print(row1)
            print(row2)
        else:
            # Cursor up 2 lines, overwrite both rows
            padded1 = row1.ljust(80)
            padded2 = row2.ljust(80)
            sys.stdout.write("\033[2A\r" + padded1 + "\n\r" + padded2)
            sys.stdout.flush()


class PricingClient:
    """
    Client for the Pricing GraphQL API.
    Use from notebooks or scripts; configurable base URL for local vs Docker.
    """

    def __init__(self, url: str = "http://api:8000/graphql", timeout: float = 30.0) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout
        self._endpoint = HTTPEndpoint(self._url, timeout=timeout)

    def _request(self, query: str, variables: dict | None = None) -> dict:
        result = self._endpoint(query, variables or {})
        if "errors" in result and result["errors"]:
            raise RuntimeError(f"GraphQL errors: {result['errors']}")
        return result.get("data", {})

    def hello(self, name: str = "World") -> str:
        """Call the hello query."""
        query = """
            query Hello($name: String!) {
                hello(name: $name)
            }
        """
        data = self._request(query, {"name": name})
        return data["hello"]

    def version(self) -> str:
        """Call the version query."""
        query = """
            query Version {
                version
            }
        """
        data = self._request(query)
        return data["version"]

    def price_zero_coupon_bond(
        self,
        bond: ZeroCouponBondInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        pv01_curve_name: str | None = None,
        pv01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a zero-coupon bond. Optionally compute PV01 (parallel curve bump)."""
        query = """
            query PriceZeroCouponBond(
                $bond: ZeroCouponBondInput!,
                $market: MarketInput!,
                $calculatePv01: Boolean,
                $pv01CurveName: String,
                $pv01BumpBp: Float
            ) {
                priceZeroCouponBond(
                    bond: $bond,
                    market: $market,
                    calculatePv01: $calculatePv01,
                    pv01CurveName: $pv01CurveName,
                    pv01BumpBp: $pv01BumpBp
                ) {
                    npv
                    riskMeasures {
                        pv01
                    }
                }
            }
        """
        variables: dict[str, Any] = {
            "bond": _bond_to_vars(bond),
            "market": _market_to_vars(market),
            "calculatePv01": calculate_pv01,
            "pv01BumpBp": pv01_bump_bp,
        }
        if pv01_curve_name is not None:
            variables["pv01CurveName"] = pv01_curve_name
        data = self._request(query, variables)
        raw = data["priceZeroCouponBond"]
        npv = raw["npv"]
        risk = raw.get("riskMeasures") or {}
        pv01 = risk.get("pv01") if risk else None
        return PricingResult(npv=npv, pv01=pv01)

    def price_cds(
        self,
        cds: CDSInput,
        market: MarketInput,
        calculate_cs01: bool = False,
        cs01_hazard_curve_name: str | None = None,
        cs01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a single-name CDS. Optionally compute CS01 (hazard curve bump)."""
        query = """
            query PriceCds(
                $cds: CDSInput!,
                $market: MarketInput!,
                $calculateCs01: Boolean,
                $cs01HazardCurveName: String,
                $cs01BumpBp: Float
            ) {
                priceCds(
                    cds: $cds,
                    market: $market,
                    calculateCs01: $calculateCs01,
                    cs01HazardCurveName: $cs01HazardCurveName,
                    cs01BumpBp: $cs01BumpBp
                ) {
                    npv
                    riskMeasures {
                        pv01
                        fxDelta
                        cs01
                    }
                }
            }
        """
        variables: dict[str, Any] = {
            "cds": _cds_to_vars(cds),
            "market": _market_to_vars(market),
            "calculateCs01": calculate_cs01,
            "cs01BumpBp": cs01_bump_bp,
        }
        if cs01_hazard_curve_name is not None:
            variables["cs01HazardCurveName"] = cs01_hazard_curve_name
        data = self._request(query, variables)
        raw = data["priceCds"]
        npv = raw["npv"]
        risk = raw.get("riskMeasures") or {}
        pv01 = risk.get("pv01") if risk else None
        fx_delta = risk.get("fxDelta") if risk else None
        cs01 = risk.get("cs01") if risk else None
        return PricingResult(npv=npv, pv01=pv01, fx_delta=fx_delta, cs01=cs01)

    def price_fx_forward(
        self,
        forward: FXForwardInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        calculate_fx_delta: bool = False,
        pv01_curve_name: str | None = None,
        pv01_bump_bp: float = 1.0,
        fx_delta_pair: str | None = None,
        fx_delta_bump_pct: float = 0.01,
    ) -> PricingResult:
        """Price an FX forward (CIP). Optionally compute PV01 and FX delta."""
        query = """
            query PriceFxForward(
                $forward: FXForwardInput!,
                $market: MarketInput!,
                $calculatePv01: Boolean,
                $calculateFxDelta: Boolean,
                $pv01CurveName: String,
                $pv01BumpBp: Float,
                $fxDeltaPair: String,
                $fxDeltaBumpPct: Float
            ) {
                priceFxForward(
                    forward: $forward,
                    market: $market,
                    calculatePv01: $calculatePv01,
                    calculateFxDelta: $calculateFxDelta,
                    pv01CurveName: $pv01CurveName,
                    pv01BumpBp: $pv01BumpBp,
                    fxDeltaPair: $fxDeltaPair,
                    fxDeltaBumpPct: $fxDeltaBumpPct
                ) {
                    npv
                    riskMeasures {
                        pv01
                        fxDelta
                    }
                }
            }
        """
        variables: dict[str, Any] = {
            "forward": _fx_forward_to_vars(forward),
            "market": _market_to_vars(market),
            "calculatePv01": calculate_pv01,
            "calculateFxDelta": calculate_fx_delta,
            "pv01BumpBp": pv01_bump_bp,
            "fxDeltaBumpPct": fx_delta_bump_pct,
        }
        if pv01_curve_name is not None:
            variables["pv01CurveName"] = pv01_curve_name
        if fx_delta_pair is not None:
            variables["fxDeltaPair"] = fx_delta_pair
        data = self._request(query, variables)
        raw = data["priceFxForward"]
        npv = raw["npv"]
        risk = raw.get("riskMeasures") or {}
        pv01 = risk.get("pv01") if risk else None
        fx_delta_val = risk.get("fxDelta") if risk else None
        return PricingResult(npv=npv, pv01=pv01, fx_delta=fx_delta_val)

    def price_swap(
        self,
        swap: FixedFloatSwapInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        pv01_curve_name: str | None = None,
        pv01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a fixed-float interest rate swap. Optionally compute PV01."""
        query = """
            query PriceSwap(
                $swap: FixedFloatSwapInput!,
                $market: MarketInput!,
                $calculatePv01: Boolean,
                $pv01CurveName: String,
                $pv01BumpBp: Float
            ) {
                priceSwap(
                    swap: $swap,
                    market: $market,
                    calculatePv01: $calculatePv01,
                    pv01CurveName: $pv01CurveName,
                    pv01BumpBp: $pv01BumpBp
                ) {
                    npv
                    riskMeasures {
                        pv01
                    }
                }
            }
        """
        variables: dict[str, Any] = {
            "swap": _swap_to_vars(swap),
            "market": _market_to_vars(market),
            "calculatePv01": calculate_pv01,
            "pv01BumpBp": pv01_bump_bp,
        }
        if pv01_curve_name is not None:
            variables["pv01CurveName"] = pv01_curve_name
        data = self._request(query, variables)
        raw = data["priceSwap"]
        npv = raw["npv"]
        risk = raw.get("riskMeasures") or {}
        pv01 = risk.get("pv01") if risk else None
        return PricingResult(npv=npv, pv01=pv01)

    def price_mortgage(
        self,
        mortgage: MortgageInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        pv01_curve_name: str | None = None,
        pv01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a level-pay mortgage. Optionally compute PV01."""
        query = """
            query PriceMortgage(
                $mortgage: MortgageInput!,
                $market: MarketInput!,
                $calculatePv01: Boolean,
                $pv01CurveName: String,
                $pv01BumpBp: Float
            ) {
                priceMortgage(
                    mortgage: $mortgage,
                    market: $market,
                    calculatePv01: $calculatePv01,
                    pv01CurveName: $pv01CurveName,
                    pv01BumpBp: $pv01BumpBp
                ) {
                    npv
                    riskMeasures {
                        pv01
                    }
                }
            }
        """
        variables: dict[str, Any] = {
            "mortgage": _mortgage_to_vars(mortgage),
            "market": _market_to_vars(market),
            "calculatePv01": calculate_pv01,
            "pv01BumpBp": pv01_bump_bp,
        }
        if pv01_curve_name is not None:
            variables["pv01CurveName"] = pv01_curve_name
        data = self._request(query, variables)
        raw = data["priceMortgage"]
        npv = raw["npv"]
        risk = raw.get("riskMeasures") or {}
        pv01 = risk.get("pv01") if risk else None
        return PricingResult(npv=npv, pv01=pv01)

    async def stream_realtime_pricing(
        self,
        bond: ZeroCouponBondInput,
        curve_name: str,
        marketdata_url: str = "ws://marketdata:8001/graphql",
        max_updates: int | None = None,
        display: bool = True,
    ) -> None:
        """
        Stream real-time NPV/PV01 as curve updates arrive. Display ticks in place.
        Runs until cancelled (Ctrl+C) or max_updates if set.
        """
        md_client = MarketdataClient(marketdata_url)
        use_jupyter = _is_jupyter()
        header = f"ZCB | {bond.curve} | {bond.maturity}Y | {bond.notional:,.0f} notional"
        sep = "-" * min(60, len(header))
        full_header = f"{header}\n{sep}"
        count = 0

        try:
            async for update in md_client.subscribe_curve_updates(curve_name):
                curve_input = curve_snapshot_to_curve_input(update.curve)
                market = MarketInput(curves=[curve_input])
                result = self.price_zero_coupon_bond(bond, market, calculate_pv01=True)
                count += 1
                pv01_val = result.pv01 if result.pv01 is not None else 0.0
                changed = [i for i, d in enumerate(update.rate_deltas_bp) if d is not None]
                line = f"NPV: {result.npv:,.2f}  PV01: {pv01_val:,.2f}  changed: {changed}"
                if display:
                    _tick_display(
                        full_header, line,
                        is_first=(count == 1),
                        use_jupyter=use_jupyter,
                    )
                if max_updates is not None and count >= max_updates:
                    break
        finally:
            if display and not use_jupyter:
                print()

    async def stream_curve_display(
        self,
        curve_name: str,
        marketdata_url: str = "ws://marketdata:8001/graphql",
        max_updates: int | None = None,
        display: bool = True,
    ) -> None:
        """
        Stream curve updates and display the curve in place (ticking). Runs until interrupted or max_updates.
        """
        md_client = MarketdataClient(marketdata_url)
        use_jupyter = _is_jupyter()
        header = f"Curve {curve_name}"
        sep = "-" * min(50, len(header) + 10)
        full_header = f"{header}\n{sep}"
        count = 0

        try:
            async for update in md_client.subscribe_curve_updates(curve_name):
                c = update.curve
                rates_pct = ", ".join(f"{r*100:.2f}%" for r in c.zero_rates_cc)
                changed = [i for i, d in enumerate(update.rate_deltas_bp) if d is not None]
                line = f"pillars {c.pillars} | rates: {rates_pct} | changed: {changed}"
                count += 1
                if display:
                    _tick_display(
                        full_header, line,
                        is_first=(count == 1),
                        use_jupyter=use_jupyter,
                    )
                if max_updates is not None and count >= max_updates:
                    break
        finally:
            if display and not use_jupyter:
                print()

    async def stream_curve_and_risk(
        self,
        curve_name: str,
        bond: ZeroCouponBondInput,
        marketdata_url: str = "ws://marketdata:8001/graphql",
        max_updates: int | None = None,
        display: bool = True,
    ) -> None:
        """
        Stream curve and product/risk in two rows. Runs until interrupted or max_updates.
        """
        md_client = MarketdataClient(marketdata_url)
        use_jupyter = _is_jupyter()
        count = 0

        try:
            async for update in md_client.subscribe_curve_updates(curve_name):
                c = update.curve
                curve_input = curve_snapshot_to_curve_input(c)
                market = MarketInput(curves=[curve_input])
                result = self.price_zero_coupon_bond(bond, market, calculate_pv01=True)
                count += 1
                rates_pct = " ".join(f"{r*100:.2f}%" for r in c.zero_rates_cc)
                changed = [i for i, d in enumerate(update.rate_deltas_bp) if d is not None]
                pv01_val = result.pv01 if result.pv01 is not None else 0.0
                row1 = f"Curve {curve_name} | pillars {c.pillars} | rates: {rates_pct} | changed: {changed}"
                row2 = f"ZCB {bond.maturity}Y {bond.notional:,.0f} notional | NPV: {result.npv:,.2f}  PV01: {pv01_val:,.2f}"
                if display:
                    _tick_display_rows(row1, row2, is_first=(count == 1), use_jupyter=use_jupyter)
                if max_updates is not None and count >= max_updates:
                    break
        finally:
            if display and not use_jupyter:
                print()
