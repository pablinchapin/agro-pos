from datetime import date

import httpx
import streamlit as st

from shared.api_client import (
    get_daily_grain_purchase_report,
    get_daily_sales_report,
    get_top_sold_products,
)
from shared.components import show_api_error

st.title("Reportes")

tab_ventas, tab_compras, tab_top = st.tabs(
    ["Ventas Diarias", "Compras de Grano", "Top Productos"]
)

with tab_ventas:
    selected_date = st.date_input("Fecha", value=date.today(), key="ventas_date")
    try:
        report = get_daily_sales_report(selected_date)
    except httpx.HTTPStatusError as e:
        show_api_error(e)
    else:
        col1, col2 = st.columns(2)
        col1.metric("Total vendido", f"Q{report['total_amount']}")
        col2.metric("Transacciones", report["transaction_count"])

        st.subheader("Top 5 productos vendidos")
        if report["top_products"]:
            st.dataframe(
                report["top_products"], hide_index=True, use_container_width=True
            )
        else:
            st.info("No hubo ventas en esta fecha.")

with tab_compras:
    selected_date = st.date_input("Fecha", value=date.today(), key="compras_date")
    try:
        report = get_daily_grain_purchase_report(selected_date)
    except httpx.HTTPStatusError as e:
        show_api_error(e)
    else:
        st.metric("Total gastado", f"Q{report['total_amount']}")

        st.subheader("Desglose por tipo de grano")
        if report["breakdown"]:
            st.dataframe(report["breakdown"], hide_index=True, use_container_width=True)
        else:
            st.info("No hubo compras de grano en esta fecha.")

with tab_top:
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Desde", value=date.today(), key="top_start_date")
    end_date = col2.date_input("Hasta", value=date.today(), key="top_end_date")

    if start_date > end_date:
        st.error("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.")
    else:
        try:
            report = get_top_sold_products(start_date, end_date)
        except httpx.HTTPStatusError as e:
            show_api_error(e)
        else:
            st.subheader(f"Top productos: {report['start_date']} a {report['end_date']}")
            if report["products"]:
                st.dataframe(
                    report["products"], hide_index=True, use_container_width=True
                )
            else:
                st.info("No hubo ventas en este rango de fechas.")
