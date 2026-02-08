"""Demo: sample USD curve, market, and price ZCB, swap, FX forward, mortgage, CDS with risks."""

from pricing.curves import HazardRateCurve, ZeroRateCurve
from pricing.market import Market
from pricing.products.bond import ZeroCouponBond
from pricing.products.cds import CDS
from pricing.products.fx import FXForward
from pricing.products.mortgage import LevelPayMortgage
from pricing.products.swap import FixedFloatSwap
from pricing.pricing import price
from pricing.risk import cs01_parallel, fx_delta, pv01_parallel


def main() -> None:
    # Sample USD curve, EUR curve (base for EURUSD), and hazard curve
    pillars = [0.5, 1.0, 2.0, 5.0, 10.0]
    usd_rates = [0.045, 0.043, 0.040, 0.038, 0.037]
    eur_rates = [0.040, 0.038, 0.036, 0.034, 0.033]  # Lower than USD for typical EURUSD fwd pts
    usd_curve = ZeroRateCurve(name="USD_DISC", pillars=pillars, zero_rates_cc=usd_rates)
    eur_curve = ZeroRateCurve(name="EUR_DISC", pillars=pillars, zero_rates_cc=eur_rates)
    hazard_curve = HazardRateCurve(
        name="CORP_HAZ",
        pillars=pillars,
        hazard_rates=[0.01] * 5,
    )

    market = Market(
        curves={"USD_DISC": usd_curve, "EUR_DISC": eur_curve, "CORP_HAZ": hazard_curve},
        fx_spot={"EURUSD": 1.08},
    )

    # 1) ZCB 2Y 1,000,000
    zcb = ZeroCouponBond(curve="USD_DISC", maturity=2.0, notional=1_000_000)
    pv_zcb = price(zcb, market)
    pv01_zcb = pv01_parallel(zcb, market, "USD_DISC", bump_bp=1.0)

    # 2) Swap 2Y semiannual notional 10,000,000 fixed 4% pay_times [0.5, 1, 1.5, 2]
    swap = FixedFloatSwap(
        curve="USD_DISC",
        notional=10_000_000,
        fixed_rate=0.04,
        pay_times=[0.5, 1.0, 1.5, 2.0],
    )
    pv_swap = price(swap, market)
    pv01_swap = pv01_parallel(swap, market, "USD_DISC", bump_bp=1.0)

    # 3) FX forward 1Y 5,000,000 EUR strike 1.085 (CIP: base=EUR, quote=USD)
    fxfwd = FXForward(
        pair="EURUSD",
        base_curve="EUR_DISC",
        quote_curve="USD_DISC",
        maturity=1.0,
        notional_base=5_000_000,
        strike=1.085,
    )
    pv_fxfwd = price(fxfwd, market)
    pv01_fxfwd = pv01_parallel(fxfwd, market, "USD_DISC", bump_bp=1.0)
    fx_delta_fxfwd = fx_delta(fxfwd, market, "EURUSD", bump_pct=0.01)

    # 4) Level-pay mortgage 5Y 500,000 USD 6% monthly
    mortgage = LevelPayMortgage(
        curve="USD_DISC",
        notional=500_000,
        annual_rate=0.06,
        term_years=5.0,
        payments_per_year=12,
    )
    pv_mortgage = price(mortgage, market)
    pv01_mortgage = pv01_parallel(mortgage, market, "USD_DISC", bump_bp=1.0)

    # 5) CDS 5Y 10,000,000 notional 100bp spread
    cds = CDS(
        discount_curve="USD_DISC",
        survival_curve="CORP_HAZ",
        notional=10_000_000,
        premium_rate=0.01,
        pay_times=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        recovery=0.4,
    )
    pv_cds = price(cds, market)
    cs01_cds = cs01_parallel(cds, market, "CORP_HAZ", bump_bp=1.0)

    print("=== Pricing Demo ===\n")
    print("Market: USD_DISC, EUR_DISC curves, EURUSD = 1.08\n")
    print("1) Zero-coupon bond (2Y, 1,000,000 USD)")
    print(f"   PV     = {pv_zcb:,.2f}")
    print(f"   PV01   = {pv01_zcb:,.2f}\n")
    print("2) Fixed-float swap (2Y semiannual, 10M notional, 4% fixed)")
    print(f"   PV     = {pv_swap:,.2f}")
    print(f"   PV01   = {pv01_swap:,.2f}\n")
    print("3) FX forward (1Y, 5M EUR, strike 1.085)")
    print(f"   PV     = {pv_fxfwd:,.2f}")
    print(f"   PV01   = {pv01_fxfwd:,.2f}")
    print(f"   FX delta ≈ {fx_delta_fxfwd:,.2f}\n")
    print("4) Level-pay mortgage (5Y, 500k USD, 6%, monthly)")
    print(f"   PV     = {pv_mortgage:,.2f}")
    print(f"   PV01   = {pv01_mortgage:,.2f}\n")
    print("5) CDS (5Y, 10M notional, 100bp spread, protection buyer)")
    print(f"   PV     = {pv_cds:,.2f}")
    print(f"   CS01   = {cs01_cds:,.2f}\n")
    print("Done.")


if __name__ == "__main__":
    main()
