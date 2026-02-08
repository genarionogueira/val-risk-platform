"""FX forward product (instrument data only; pricing via PricingEngine)."""

from dataclasses import dataclass


@dataclass
class FXForward:
    """
    FX forward: notional_base in base currency, strike (quote per base), settle at maturity.
    Valuation uses covered interest rate parity (CIP): F = spot * DF_base(T) / DF_quote(T),
    PV in quote currency = notional_base * DF_quote(T) * (F - strike).
    pair is e.g. 'EURUSD' (base EUR, quote USD).
    """

    pair: str
    base_curve: str
    quote_curve: str
    maturity: float
    notional_base: float
    strike: float
