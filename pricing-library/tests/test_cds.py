"""Tests for CDS and CS01."""

from pricing.curves import HazardRateCurve, ZeroRateCurve
from pricing.market import Market
from pricing.pricers.cds_pricer import CDSPricer
from pricing.products.cds import CDS
from pricing.pricing import price
from pricing.risk import cs01_parallel


def test_cds_at_fair_spread_near_zero_pv() -> None:
    """When premium_rate equals fair spread, NPV should be near zero (protection buyer)."""
    pillars = [0.5, 1.0, 1.5, 2.0]
    disc_curve = ZeroRateCurve(
        name="USD_DISC",
        pillars=pillars,
        zero_rates_cc=[0.04] * 4,
    )
    hazard_curve = HazardRateCurve(
        name="CORP_HAZ",
        pillars=pillars,
        hazard_rates=[0.01, 0.01, 0.01, 0.01],
    )
    market = Market(curves={"USD_DISC": disc_curve, "CORP_HAZ": hazard_curve})

    cds = CDS(
        discount_curve="USD_DISC",
        survival_curve="CORP_HAZ",
        notional=10_000_000,
        premium_rate=0.0,  # placeholder
        pay_times=[0.5, 1.0, 1.5, 2.0],
        recovery=0.4,
    )
    fair = CDSPricer.fair_spread(cds, market)
    cds_at_fair = CDS(
        discount_curve="USD_DISC",
        survival_curve="CORP_HAZ",
        notional=10_000_000,
        premium_rate=fair,
        pay_times=[0.5, 1.0, 1.5, 2.0],
        recovery=0.4,
    )
    pv = price(cds_at_fair, market)
    assert abs(pv) < 0.01 * 10_000_000


def test_cs01_protection_buyer_positive() -> None:
    """For protection buyer: bumping hazard up increases default prob => PV up => CS01 > 0."""
    pillars = [0.5, 1.0, 2.0]
    disc_curve = ZeroRateCurve(
        name="USD_DISC",
        pillars=pillars,
        zero_rates_cc=[0.04] * 3,
    )
    hazard_curve = HazardRateCurve(
        name="CORP_HAZ",
        pillars=pillars,
        hazard_rates=[0.01, 0.01, 0.01],
    )
    market = Market(curves={"USD_DISC": disc_curve, "CORP_HAZ": hazard_curve})

    cds = CDS(
        discount_curve="USD_DISC",
        survival_curve="CORP_HAZ",
        notional=10_000_000,
        premium_rate=0.005,
        pay_times=[0.5, 1.0, 2.0],
        recovery=0.4,
        protection_buyer=True,
    )
    cs01 = cs01_parallel(cds, market, "CORP_HAZ", bump_bp=1.0)
    assert cs01 > 0
