import httpx
import streamlit as st

from shared.api_client import decode_token, login


def login_page() -> None:
    st.title("Agro POS — Iniciar Sesión")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        try:
            data = login(username, password)
        except httpx.HTTPStatusError:
            st.error("Usuario o contraseña incorrectos")
        else:
            st.session_state.access_token = data["access_token"]
            st.session_state.username = username
            st.session_state.role = decode_token(data["access_token"]).get("role")
            st.rerun()
