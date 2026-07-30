from datetime import date
from typing import Optional

import httpx
import streamlit as st
from jose import jwt

BASE_URL = "http://localhost:8000/api/v1"


@st.cache_resource
def get_client() -> httpx.Client:
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


def get_headers() -> dict:
    token = st.session_state.get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


def decode_token(token: str) -> dict:
    """Reads the role/username out of the JWT without verifying the signature.

    The signature is verified by the backend on every request; this is
    purely so the frontend knows which nav sections to render.
    """
    return jwt.get_unverified_claims(token)


def _handle_response(response: httpx.Response):
    if response.status_code == 401:
        st.session_state.clear()
        st.rerun()
    response.raise_for_status()
    return response.json() if response.content else None


# --- Auth ---

def login(username: str, password: str) -> dict:
    response = get_client().post(
        "/auth/token",
        data={"username": username, "password": password},
    )
    response.raise_for_status()
    return response.json()


# --- Products ---

def get_products() -> list[dict]:
    response = get_client().get("/products/", headers=get_headers())
    return _handle_response(response)


def create_product(payload: dict) -> dict:
    response = get_client().post("/products/", json=payload, headers=get_headers())
    return _handle_response(response)


def update_product(product_id: int, payload: dict) -> dict:
    response = get_client().patch(
        f"/products/{product_id}", json=payload, headers=get_headers()
    )
    return _handle_response(response)


def delete_product(product_id: int) -> None:
    response = get_client().delete(f"/products/{product_id}", headers=get_headers())
    _handle_response(response)


# --- Inventory ---

def get_product_inventory() -> list[dict]:
    response = get_client().get("/inventory/products", headers=get_headers())
    return _handle_response(response)


def get_grain_inventory() -> list[dict]:
    response = get_client().get("/inventory/grains", headers=get_headers())
    return _handle_response(response)


# --- Reports ---

def get_daily_sales_report(report_date: Optional[date] = None) -> dict:
    params = {"date": report_date.isoformat()} if report_date else {}
    response = get_client().get(
        "/reports/sales/daily", params=params, headers=get_headers()
    )
    return _handle_response(response)


def get_daily_grain_purchase_report(report_date: Optional[date] = None) -> dict:
    params = {"date": report_date.isoformat()} if report_date else {}
    response = get_client().get(
        "/reports/grain-purchases/daily", params=params, headers=get_headers()
    )
    return _handle_response(response)


def get_top_sold_products(
    start_date: Optional[date] = None, end_date: Optional[date] = None
) -> dict:
    params = {}
    if start_date:
        params["start_date"] = start_date.isoformat()
    if end_date:
        params["end_date"] = end_date.isoformat()
    response = get_client().get(
        "/reports/products/top-sold", params=params, headers=get_headers()
    )
    return _handle_response(response)
