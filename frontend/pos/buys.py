from datetime import date

import httpx
import streamlit as st

from shared.api_client import (
    create_grain_purchase,
    get_grain_inventory,
    get_persons_by_role,
)
from shared.components import show_api_error
from shared.translations import t

st.title(t("grain_purchase.title"))

if "gp_farmer_id" not in st.session_state:
    st.session_state.gp_farmer_id = None
if "gp_weight" not in st.session_state:
    st.session_state.gp_weight = 1.0
if "gp_price" not in st.session_state:
    st.session_state.gp_price = 1.0
if "gp_grain_id" not in st.session_state:
    st.session_state.gp_grain_id = None


@st.cache_data(ttl=60)
def _load_farmers() -> list[dict]:
    return get_persons_by_role("farmer")


@st.cache_data(ttl=60)
def _load_grain_types() -> list[dict]:
    return get_grain_inventory()


farmers = _load_farmers()

if not farmers:
    st.warning(t("grain_purchase.no_farmer"))
    st.session_state.gp_farmer_id = None
else:
    farmer = st.selectbox(
        t("grain_purchase.select_farmer"),
        options=farmers,
        format_func=lambda p: f"{p['full_name']} ({p['phone'] or '-'})",
    )
    st.session_state.gp_farmer_id = farmer["id"]

st.divider()

grain_types = _load_grain_types()

if not grain_types:
    st.info(t("grain_purchase.no_grains"))
else:
    selected_grain = st.selectbox(
        t("grain_purchase.select_grain"),
        options=grain_types,
        format_func=lambda g: f"{g['grain_type_name']} ({g['unit']})",
    )
    st.session_state.gp_grain_id = selected_grain["grain_type_id"]

    weight = st.number_input(
        t("grain_purchase.weight"),
        min_value=0.01,
        step=0.5,
        format="%.2f",
        key="gp_weight",
    )
    price_per_unit = st.number_input(
        t("grain_purchase.price_per_unit"),
        min_value=0.01,
        step=0.50,
        format="%.2f",
        key="gp_price",
    )

    total = weight * price_per_unit
    st.metric(t("grain_purchase.calculated_total"), f"Q{total:.2f}")

    st.divider()

    no_farmer = st.session_state.gp_farmer_id is None
    invalid_amounts = weight <= 0 or price_per_unit <= 0

    if no_farmer:
        st.caption(t("grain_purchase.no_farmer"))

    if st.button(
        t("grain_purchase.confirm"),
        type="primary",
        disabled=no_farmer or invalid_amounts,
    ):
        payload = {
            "person_id": st.session_state.gp_farmer_id,
            "grain_type_id": st.session_state.gp_grain_id,
            "weight": str(weight),
            "price_per_unit": str(price_per_unit),
            "date": date.today().isoformat(),
        }
        try:
            create_grain_purchase(payload)
        except httpx.HTTPStatusError as e:
            show_api_error(e)
        else:
            st.success(t("grain_purchase.success"))
            st.session_state.gp_farmer_id = None
            st.session_state.gp_grain_id = None
            st.session_state.pop("gp_weight", None)
            st.session_state.pop("gp_price", None)
            st.cache_data.clear()
            st.rerun()
