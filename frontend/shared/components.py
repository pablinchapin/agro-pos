import httpx
import streamlit as st


def show_api_error(exc: httpx.HTTPStatusError) -> None:
    try:
        detail = exc.response.json().get("detail", "Ocurrió un error inesperado.")
    except ValueError:
        detail = "Ocurrió un error inesperado."
    st.error(detail)
