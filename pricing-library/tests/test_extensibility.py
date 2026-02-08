"""Tests for extensibility: custom pricers, custom curves, risk measure composability."""

from dataclasses import dataclass

import pytest

from pricing.curves import HazardRateCurve, ZeroRateCurve
from pricing.engine import PricingEngine, create_default_engine
from pricing.market import Market
from pricing.pricers.base import BasePricer
from pricing.pricing import price
from pricing.risk import PV01Parallel, FXDelta, pv01_parallel, fx_delta


def test_custom_pricer_registration() -> None:
    """Custom pricers can be registered with the engine and used for dispatch."""

    @dataclass
    class CustomInstrument:
        """Minimal instrument for testing."""
        value: float

    class CustomPricer(BasePricer):
        def can_price(self, instrument) -> bool:
            return isinstance(instrument, CustomInstrument)

        def npv(self, instrument, market: Market) -> float:
            assert isinstance(instrument, CustomInstrument)
            return instrument.value

    curve = ZeroRateCurve(name="C", pillars=[1.0], zero_rates_cc=[0.04])
    market = Market(curves={"C": curve})

    engine = PricingEngine()
    engine.register(CustomPricer())

    custom = CustomInstrument(value=100.0)
    result = engine.npv(custom, market)
    assert result == 100.0


def test_default_engine_has_builtin_pricers() -> None:
    """create_default_engine() returns engine that prices ZCB, swap, FX, mortgage, CDS."""
    curve = ZeroRateCurve(name="USD", pillars=[0.5, 1.0, 2.0], zero_rates_cc=[0.045, 0.043, 0.04])
    eur_curve = ZeroRateCurve(name="EUR", pillars=[0.5, 1.0, 2.0], zero_rates_cc=[0.04, 0.038, 0.036])
    hazard = HazardRateCurve(name="HAZ", pillars=[0.5, 1.0, 2.0], hazard_rates=[0.01, 0.01, 0.01])
    market = Market(curves={"USD": curve, "EUR": eur_curve, "HAZ": hazard}, fx_spot={"EURUSD": 1.08})

    engine = create_default_engine()

    from pricing.products.bond import ZeroCouponBond
    from pricing.products.cds import CDS
    from pricing.products.fx import FXForward
    from pricing.products.mortgage import LevelPayMortgage
    from pricing.products.swap import FixedFloatSwap

    bond = ZeroCouponBond(curve="USD", maturity=1.0, notional=1_000_000)
    assert engine.npv(bond, market) == price(bond, market)

    swap = FixedFloatSwap(curve="USD", notional=10_000_000, fixed_rate=0.04, pay_times=[0.5, 1.0, 1.5, 2.0])
    assert engine.npv(swap, market) == price(swap, market)

    fwd = FXForward(
        pair="EURUSD",
        base_curve="EUR",
        quote_curve="USD",
        maturity=1.0,
        notional_base=5_000_000,
        strike=1.085,
    )
    assert engine.npv(fwd, market) == price(fwd, market)

    mortgage = LevelPayMortgage(curve="USD", notional=500_000, annual_rate=0.06, term_years=5.0, payments_per_year=12)
    assert engine.npv(mortgage, market) == price(mortgage, market)

    cds = CDS(
        discount_curve="USD",
        survival_curve="HAZ",
        notional=10_000_000,
        premium_rate=0.005,
        pay_times=[0.5, 1.0, 2.0],
    )
    assert engine.npv(cds, market) == price(cds, market)


def test_custom_curve_implementation() -> None:
    """Market accepts any object that implements the Curve protocol (structural typing)."""

    class FlatCurve:
        """Minimal curve: flat discount factor."""
        name = "FLAT"

        def df(self, t: float) -> float:
            return 0.95

        def bumped(self, bump: float) -> "FlatCurve":
            return self

    market = Market(curves={"FLAT": FlatCurve()})
    assert market.curve("FLAT").df(1.0) == 0.95

    # Pricing a ZCB with this curve requires the curve to be in market; bond references "FLAT"
    from pricing.products.bond import ZeroCouponBond
    bond = ZeroCouponBond(curve="FLAT", maturity=1.0, notional=100.0)
    pv = price(bond, market)
    assert abs(pv - 100.0 * 0.95) < 1e-9


def test_unknown_instrument_raises() -> None:
    """Engine raises clear error when no pricer is registered for instrument type."""

    @dataclass
    class UnregisteredInstrument:
        pass

    curve = ZeroRateCurve(name="C", pillars=[1.0], zero_rates_cc=[0.04])
    market = Market(curves={"C": curve})
    engine = PricingEngine()

    with pytest.raises(ValueError, match="No pricer registered"):
        engine.npv(UnregisteredInstrument(), market)


def test_risk_measure_classes_composable() -> None:
    """PV01Parallel and FXDelta can be used as first-class risk measure objects."""
    eur = ZeroRateCurve(name="EUR", pillars=[1.0, 2.0], zero_rates_cc=[0.04, 0.04])
    usd = ZeroRateCurve(name="USD", pillars=[1.0, 2.0], zero_rates_cc=[0.04, 0.04])
    market = Market(curves={"EUR": eur, "USD": usd}, fx_spot={"EURUSD": 1.08})

    from pricing.products.bond import ZeroCouponBond
    from pricing.products.fx import FXForward

    bond = ZeroCouponBond(curve="USD", maturity=1.5, notional=1_000_000)
    fwd = FXForward(
        pair="EURUSD",
        base_curve="EUR",
        quote_curve="USD",
        maturity=1.0,
        notional_base=5_000_000,
        strike=1.085,
    )

    pv01_measure = PV01Parallel(curve_name="USD", bump_bp=1.0)
    fx_delta_measure = FXDelta(pair="EURUSD", bump_pct=0.01)

    # Same results as legacy functions
    assert pv01_measure.name == "PV01_USD"
    assert fx_delta_measure.name == "FXDelta_EURUSD"

    assert abs(pv01_measure.compute(bond, market) - pv01_parallel(bond, market, "USD", bump_bp=1.0)) < 1e-10
    assert abs(fx_delta_measure.compute(fwd, market) - fx_delta(fwd, market, "EURUSD", bump_pct=0.01)) < 1e-10
