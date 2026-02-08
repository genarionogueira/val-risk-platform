"""Integration tests for GraphQL pricing and risk queries."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_price_zero_coupon_bond_matches_demo():
    """ZCB pricing and PV01 match pricing-library demo output."""
    query = """
    query PriceZCB {
      priceZeroCouponBond(
        bond: {
          curve: "USD_DISC"
          maturity: 2.0
          notional: 1000000
        }
        market: {
          curves: [{
            name: "USD_DISC"
            pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
            zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
          }]
        }
        calculatePv01: true
      ) {
        npv
        riskMeasures {
          pv01
        }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    result = data["data"]["priceZeroCouponBond"]
    assert abs(result["npv"] - 923_116.35) < 1.0
    assert result["riskMeasures"]["pv01"] is not None
    assert abs(result["riskMeasures"]["pv01"] - (-184.60)) < 1.0


def test_price_zero_coupon_bond_missing_curve_returns_error():
    """Request with curve not in market returns validation error."""
    query = """
    query {
      priceZeroCouponBond(
        bond: { curve: "MISSING", maturity: 2.0, notional: 1000000 }
        market: {
          curves: [{
            name: "USD_DISC"
            pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
            zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
          }]
        }
      ) { npv }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert any("curve" in e["message"].lower() for e in data["errors"])


def test_price_zero_coupon_bond_negative_maturity_returns_error():
    """Negative maturity returns validation error."""
    query = """
    query {
      priceZeroCouponBond(
        bond: { curve: "USD_DISC", maturity: -1.0, notional: 1000000 }
        market: {
          curves: [{
            name: "USD_DISC"
            pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
            zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
          }]
        }
      ) { npv }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data


def test_price_cds_returns_npv_and_cs01():
    """CDS pricing and CS01 work with discount + hazard curves."""
    query = """
    query PriceCds {
      priceCds(
        cds: {
          discountCurve: "USD_DISC"
          survivalCurve: "CORP_HAZ"
          notional: 10000000
          premiumRate: 0.01
          payTimes: [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
          recovery: 0.4
        }
        market: {
          curves: [{
            name: "USD_DISC"
            pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
            zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037]
          }]
          hazardCurves: [{
            name: "CORP_HAZ"
            pillars: [0.5, 1.0, 2.0, 5.0, 10.0]
            hazardRates: [0.01, 0.01, 0.01, 0.01, 0.01]
          }]
        }
        calculateCs01: true
      ) {
        npv
        riskMeasures {
          cs01
        }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    result = data["data"]["priceCds"]
    assert "npv" in result
    assert result["riskMeasures"]["cs01"] is not None
    assert abs(result["npv"] - (-171_924.01)) < 500.0  # Match demo ballpark


def test_price_fx_forward_cip():
    """FX forward (CIP) pricing and risk work with base + quote curves."""
    query = """
    query PriceFxForward {
      priceFxForward(
        forward: {
          pair: "EURUSD"
          baseCurve: "EUR_DISC"
          quoteCurve: "USD_DISC"
          maturity: 1.0
          notionalBase: 5000000
          strike: 1.085
        }
        market: {
          curves: [
            { name: "EUR_DISC", pillars: [0.5, 1.0, 2.0, 5.0, 10.0], zeroRatesCc: [0.040, 0.038, 0.036, 0.034, 0.033] }
            { name: "USD_DISC", pillars: [0.5, 1.0, 2.0, 5.0, 10.0], zeroRatesCc: [0.045, 0.043, 0.040, 0.038, 0.037] }
          ]
          fxSpot: [{ pair: "EURUSD", spot: 1.08 }]
        }
        calculatePv01: true
        calculateFxDelta: true
      ) {
        npv
        riskMeasures {
          pv01
          fxDelta
        }
      }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    result = data["data"]["priceFxForward"]
    assert "npv" in result
    assert result["riskMeasures"]["pv01"] is not None
    assert result["riskMeasures"]["fxDelta"] is not None
    # Match demo output (CIP: NPV ~1980, PV01 ~520, FX delta ~4.8M)
    assert abs(result["npv"] - 1_980.59) < 10.0
    assert abs(result["riskMeasures"]["pv01"] - 519.64) < 10.0
    assert abs(result["riskMeasures"]["fxDelta"] - 4_813_564.70) < 10_000.0


def test_price_fx_forward_missing_base_curve_returns_error():
    """FX forward with missing base curve returns validation error."""
    query = """
    query {
      priceFxForward(
        forward: {
          pair: "EURUSD"
          baseCurve: "EUR_DISC"
          quoteCurve: "USD_DISC"
          maturity: 1.0
          notionalBase: 5000000
          strike: 1.085
        }
        market: {
          curves: [{ name: "USD_DISC", pillars: [1.0], zeroRatesCc: [0.04] }]
          fxSpot: [{ pair: "EURUSD", spot: 1.08 }]
        }
      ) { npv }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert any("base" in e["message"].lower() or "eur_disc" in e["message"].lower() for e in data["errors"])


def test_price_fx_forward_missing_quote_curve_returns_error():
    """FX forward with missing quote curve returns validation error."""
    query = """
    query {
      priceFxForward(
        forward: {
          pair: "EURUSD"
          baseCurve: "EUR_DISC"
          quoteCurve: "USD_DISC"
          maturity: 1.0
          notionalBase: 5000000
          strike: 1.085
        }
        market: {
          curves: [{ name: "EUR_DISC", pillars: [1.0], zeroRatesCc: [0.04] }]
          fxSpot: [{ pair: "EURUSD", spot: 1.08 }]
        }
      ) { npv }
    }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert any("quote" in e["message"].lower() or "usd_disc" in e["message"].lower() for e in data["errors"])


def test_hello_and_version():
    """Legacy hello and version queries still work."""
    response = client.post(
        "/graphql",
        json={"query": "{ hello(name: \"API\") version }"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["hello"] == "Hello API from Pricing API!"
    assert data["data"]["version"] == "0.1.0"
