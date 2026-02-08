"""GraphQL schema: pricing and risk queries."""

from typing import Optional

import strawberry

from app.services import (
    price_cds,
    price_fx_forward,
    price_mortgage,
    price_swap,
    price_zero_coupon_bond,
)
from app.types import (
    CDSInput,
    FXForwardInput,
    FixedFloatSwapInput,
    MarketInput,
    MortgageInput,
    PricingResult,
    ZeroCouponBondInput,
)


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str = "World") -> str:
        return f"Hello {name} from Pricing API!"

    @strawberry.field
    def version(self) -> str:
        return "0.1.0"

    @strawberry.field
    def price_zero_coupon_bond(
        self,
        bond: ZeroCouponBondInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        pv01_curve_name: Optional[str] = None,
        pv01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a zero-coupon bond. Optionally compute PV01 (parallel curve bump)."""
        return price_zero_coupon_bond(
            bond=bond,
            market=market,
            calculate_pv01=calculate_pv01,
            pv01_curve_name=pv01_curve_name,
            pv01_bump_bp=pv01_bump_bp,
        )

    @strawberry.field
    def price_swap(
        self,
        swap: FixedFloatSwapInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        pv01_curve_name: Optional[str] = None,
        pv01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a fixed-float interest rate swap. Optionally compute PV01."""
        return price_swap(
            swap=swap,
            market=market,
            calculate_pv01=calculate_pv01,
            pv01_curve_name=pv01_curve_name,
            pv01_bump_bp=pv01_bump_bp,
        )

    @strawberry.field
    def price_fx_forward(
        self,
        forward: FXForwardInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        calculate_fx_delta: bool = False,
        pv01_curve_name: Optional[str] = None,
        pv01_bump_bp: float = 1.0,
        fx_delta_pair: Optional[str] = None,
        fx_delta_bump_pct: float = 0.01,
    ) -> PricingResult:
        """Price an FX forward. Optionally compute PV01 and FX delta."""
        return price_fx_forward(
            forward=forward,
            market=market,
            calculate_pv01=calculate_pv01,
            calculate_fx_delta=calculate_fx_delta,
            pv01_curve_name=pv01_curve_name,
            pv01_bump_bp=pv01_bump_bp,
            fx_delta_pair=fx_delta_pair,
            fx_delta_bump_pct=fx_delta_bump_pct,
        )

    @strawberry.field
    def price_mortgage(
        self,
        mortgage: MortgageInput,
        market: MarketInput,
        calculate_pv01: bool = False,
        pv01_curve_name: Optional[str] = None,
        pv01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a level-pay mortgage. Optionally compute PV01."""
        return price_mortgage(
            mortgage=mortgage,
            market=market,
            calculate_pv01=calculate_pv01,
            pv01_curve_name=pv01_curve_name,
            pv01_bump_bp=pv01_bump_bp,
        )

    @strawberry.field
    def price_cds(
        self,
        cds: CDSInput,
        market: MarketInput,
        calculate_cs01: bool = False,
        cs01_hazard_curve_name: Optional[str] = None,
        cs01_bump_bp: float = 1.0,
    ) -> PricingResult:
        """Price a single-name CDS. Optionally compute CS01 (hazard curve bump)."""
        return price_cds(
            cds=cds,
            market=market,
            calculate_cs01=calculate_cs01,
            cs01_hazard_curve_name=cs01_hazard_curve_name,
            cs01_bump_bp=cs01_bump_bp,
        )


schema = strawberry.Schema(query=Query)
