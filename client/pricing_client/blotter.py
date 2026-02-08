"""Live blotter table component for Jupyter: display-only widget and streaming helper."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    import ipywidgets as widgets
except ImportError:
    widgets = None  # type: ignore[assignment]

try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore[assignment]

from pricing_client.marketdata import MarketdataClient
from pricing_client.types import (
    CurveInput,
    FxSpotInput,
    HazardCurveInput,
    MarketInput,
    curve_snapshot_to_curve_input,
)

if TYPE_CHECKING:
    from pricing_client.client import PricingClient
    from pricing_client.types import PricingResult


def _ensure_widgets() -> None:
    if widgets is None:
        raise ImportError(
            "LiveBlotter requires ipywidgets. Install with: pip install ipywidgets"
        )


def _ensure_pandas() -> None:
    if pd is None:
        raise ImportError(
            "LiveBlotter requires pandas. Install with: pip install pandas"
        )


def _format_blotter_df(df: "pd.DataFrame") -> Any:
    """Format DataFrame for professional display: numeric columns right-aligned, thousands + 2 decimals."""
    _ensure_pandas()
    numeric_cols = ["NPV", "PV01", "FX_delta", "CS01"]
    subset = [c for c in numeric_cols if c in df.columns]
    formatters = {c: "{:,.2f}" for c in subset}
    styled = df.style.format(formatters, na_rep="—")
    if subset:
        styled = styled.set_properties(
            subset=subset,
            **{"text-align": "right"},
        )
    return styled


class LiveBlotter:
    """
    Display-only live blotter: ipywidgets VBox with title, status label, and table.
    Call display(blotter.widget) once, then update(rows, status_text) on each tick.
    """

    def __init__(self, title: str = "Live pricing") -> None:
        _ensure_widgets()
        self._title = title
        self._header = widgets.HTML(value=f"<b>{title}</b>")
        self._status_label = widgets.Label(value="Waiting for ticks…")
        self._out = widgets.Output(
            layout=widgets.Layout(height="auto", border="1px solid #ccc")
        )
        self._widget = widgets.VBox([self._header, self._status_label, self._out])

    @property
    def widget(self) -> Any:
        """The ipywidgets VBox to display once with display(blotter.widget)."""
        return self._widget

    def update(self, rows: list[dict[str, Any]] | Any, status_text: str = "") -> None:
        """
        Refresh the table and status. rows: list of dicts (Product, NPV, PV01, FX_delta, CS01) or DataFrame.
        """
        _ensure_widgets()
        _ensure_pandas()
        if not isinstance(rows, pd.DataFrame):
            df = pd.DataFrame(rows)
        else:
            df = rows.copy()
        self._status_label.value = status_text
        styled = _format_blotter_df(df)
        from IPython.display import display
        with self._out:
            self._out.clear_output(wait=True)
            display(styled)


async def stream_live_blotter(
    client: "PricingClient",
    blotter: LiveBlotter,
    products: list[tuple[str, Any, Any]],
    *,
    static_curves: list[CurveInput],
    hazard_curves: list[HazardCurveInput] | None = None,
    fx_spot: list[FxSpotInput] | None = None,
    live_curve_name: str = "USD_DISC",
    marketdata_url: str = "ws://marketdata:8001/graphql",
    max_updates: int | None = None,
) -> None:
    """
    Subscribe to live curve updates, price all products each tick, and update the blotter.
    products: list of (label, product_input, price_fn) where price_fn(client, market) -> PricingResult.
    """
    hazard_curves = hazard_curves or []
    fx_spot = fx_spot or []
    md_client = MarketdataClient(marketdata_url)
    count = 0
    async for update in md_client.subscribe_curve_updates(live_curve_name):
        live_curve = curve_snapshot_to_curve_input(update.curve)
        market = MarketInput(
            curves=[live_curve] + list(static_curves),
            hazard_curves=hazard_curves if hazard_curves else None,
            fx_spot=fx_spot if fx_spot else None,
        )
        rows = []
        for label, _product_input, price_fn in products:
            result: "PricingResult" = price_fn(client, market)
            rows.append({
                "Product": label,
                "NPV": result.npv,
                "PV01": result.pv01,
                "FX_delta": result.fx_delta,
                "CS01": result.cs01,
            })
        changed = [i for i, d in enumerate(update.rate_deltas_bp) if d is not None]
        status_text = f"Tick #{count + 1} | changed: {changed}"
        blotter.update(rows, status_text=status_text)
        count += 1
        if max_updates is not None and count >= max_updates:
            break
