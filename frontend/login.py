import httpx
import streamlit as st

from shared.api_client import decode_token, login
from shared.translations import t


def login_page() -> None:
    st.title(f"Agro POS — {t('nav.login')}")

    username = st.text_input(t("auth.username"))
    password = st.text_input(t("auth.password"), type="password")

    if st.button(t("auth.login_button")):
        try:
            data = login(username, password)
        except httpx.HTTPStatusError:
            st.error(t("auth.login_error"))
        else:
            st.session_state.access_token = data["access_token"]
            st.session_state.username = username
            st.session_state.role = decode_token(data["access_token"]).get("role")
            st.rerun()
