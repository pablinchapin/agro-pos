import httpx
import streamlit as st

from shared.api_client import get_grain_inventory, get_product_inventory
from shared.components import show_api_error

st.title("Inventario")

tab_productos, tab_granos = st.tabs(["Productos", "Granos"])

with tab_productos:
    try:
        products = get_product_inventory()
    except httpx.HTTPStatusError as e:
        show_api_error(e)
        products = []

    if not products:
        st.info("No hay productos registrados.")
    else:
        low_stock = [p for p in products if p["low_stock"]]
        if low_stock:
            st.warning(f"⚠️ {len(low_stock)} producto(s) con stock bajo")
            for p in low_stock:
                st.error(
                    f"**{p['name']}** — stock: {p['stock']} {p['unit']} "
                    f"(mínimo: {p['min_stock']})"
                )
            st.divider()

        st.dataframe(products, hide_index=True, use_container_width=True)

with tab_granos:
    try:
        grains = get_grain_inventory()
    except httpx.HTTPStatusError as e:
        show_api_error(e)
        grains = []

    if not grains:
        st.info("No hay tipos de grano registrados.")
    else:
        st.dataframe(grains, hide_index=True, use_container_width=True)
