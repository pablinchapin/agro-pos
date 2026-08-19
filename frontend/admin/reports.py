from datetime import date

import httpx
import streamlit as st

from shared.api_client import (
    get_daily_grain_purchase_report,
    get_daily_sales_report,
    get_top_sold_products,
)
from shared.components import show_api_error
from shared.translations import t

st.title(t("report.title"))

tab_ventas, tab_compras, tab_top = st.tabs(
    [t("report.tab_sales"), t("report.tab_grains"), t("report.tab_top")]
)

with tab_ventas:
    selected_date = st.date_input(t("report.date"), value=date.today(), key="ventas_date")
    try:
        report = get_daily_sales_report(selected_date)
    except httpx.HTTPStatusError as e:
        show_api_error(e)
    else:
        col1, col2 = st.columns(2)
        col1.metric(t("report.total_sold"), f"Q{report['total_amount']}")
        col2.metric(t("report.transactions"), report["transaction_count"])

        st.subheader(t("report.top_products").format(n=5))
        if report["top_products"]:
            top_products = [
                {
                    "product_name": p["product_name"],
                    "unit": p["unit"],
                    "quantity_sold": p["quantity_sold"],
                    "total_revenue": p["total_revenue"],
                }
                for p in report["top_products"]
            ]
            st.dataframe(
                top_products,
                hide_index=True,
                width='stretch',
                column_config=t("report.columns_sales"),
            )
        else:
            st.info(t("report.no_sales"))

with tab_compras:
    selected_date = st.date_input(t("report.date"), value=date.today(), key="compras_date")
    try:
        report = get_daily_grain_purchase_report(selected_date)
    except httpx.HTTPStatusError as e:
        show_api_error(e)
    else:
        st.metric(t("report.total_spent"), f"Q{report['total_amount']}")

        st.subheader(t("report.breakdown"))
        if report["breakdown"]:
            breakdown = [
                {
                    "grain_type_name": b["grain_type_name"],
                    "unit": b["unit"],
                    "total_weight": b["total_weight"],
                    "total_spent": b["total_spent"],
                }
                for b in report["breakdown"]
            ]
            st.dataframe(
                breakdown,
                hide_index=True,
                width='stretch',
                column_config=t("report.columns_grains"),
            )
        else:
            st.info(t("report.no_grain_purchases"))

with tab_top:
    col1, col2 = st.columns(2)
    start_date = col1.date_input(t("report.from"), value=date.today(), key="top_start_date")
    end_date = col2.date_input(t("report.to"), value=date.today(), key="top_end_date")

    if start_date > end_date:
        st.error(t("report.date_range_error"))
    else:
        try:
            report = get_top_sold_products(start_date, end_date)
        except httpx.HTTPStatusError as e:
            show_api_error(e)
        else:
            st.subheader(
                t("report.top_range").format(
                    start=report["start_date"], end=report["end_date"]
                )
            )
            if report["products"]:
                top_products = [
                    {
                        "product_name": p["product_name"],
                        "unit": p["unit"],
                        "quantity_sold": p["quantity_sold"],
                        "total_revenue": p["total_revenue"],
                    }
                    for p in report["products"]
                ]
                st.dataframe(
                    top_products,
                    hide_index=True,
                    width='stretch',
                    column_config=t("report.columns_sales"),
                )
            else:
                st.info(t("report.no_sales_range"))
