import httpx
import streamlit as st

from shared.api_client import get_grain_inventory, get_product_inventory
from shared.components import show_api_error
from shared.translations import t

st.title(t("inventory.title"))

tab_productos, tab_granos = st.tabs([t("inventory.tab_products"), t("inventory.tab_grains")])

with tab_productos:
    try:
        products = get_product_inventory()
    except httpx.HTTPStatusError as e:
        show_api_error(e)
        products = []

    if not products:
        st.info(t("inventory.none_products"))
    else:
        low_stock = [p for p in products if p["low_stock"]]
        if low_stock:
            st.warning(f"⚠️ {t('inventory.low_stock_alert').format(count=len(low_stock))}")
            for p in low_stock:
                st.error(
                    t("inventory.low_stock_detail").format(
                        name=p["name"], stock=p["stock"], unit=p["unit"], min_stock=p["min_stock"]
                    )
                )
            st.divider()

        category_labels = t("category")
        low_stock_yes = t("inventory.low_stock_yes")
        low_stock_no = t("inventory.low_stock_no")
        display_products = [
            {
                "name": p["name"],
                "category": category_labels.get(p["category"], p["category"]),
                "unit": p["unit"],
                "stock": p["stock"],
                "min_stock": p["min_stock"],
                "low_stock": low_stock_yes if p["low_stock"] else low_stock_no,
            }
            for p in products
        ]
        st.dataframe(
            display_products,
            hide_index=True,
            width='stretch',
            column_config=t("inventory.columns_products"),
        )

with tab_granos:
    try:
        grains = get_grain_inventory()
    except httpx.HTTPStatusError as e:
        show_api_error(e)
        grains = []

    if not grains:
        st.info(t("inventory.none_grains"))
    else:
        display_grains = [
            {
                "grain_type_name": g["grain_type_name"],
                "unit": g["unit"],
                "total_stock": g["total_stock"],
            }
            for g in grains
        ]
        st.dataframe(
            display_grains,
            hide_index=True,
            width='stretch',
            column_config=t("inventory.columns_grains"),
        )
