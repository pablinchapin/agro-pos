import streamlit as st

from login import login_page
from shared.translations import LANGUAGES, get_language, t

if "access_token" not in st.session_state:
    login_page()
    st.stop()

role = st.session_state.get("role")

with st.sidebar:
    selected_label = next(
        k for k, v in LANGUAGES.items() if v == get_language()
    )
    lang_choice = st.selectbox(
        "🌐 Language / Idioma",
        options=list(LANGUAGES.keys()),
        index=list(LANGUAGES.keys()).index(selected_label),
    )
    st.session_state.language = LANGUAGES[lang_choice]

    st.caption(
        t("auth.user_label").format(
            username=st.session_state.get("username", ""), role=role
        )
    )
    if st.button(t("nav.logout")):
        st.session_state.clear()
        st.rerun()

pos_ventas = st.Page("pos/sales.py", title=t("nav.sales"), icon="🛒")
pos_compra = st.Page("pos/buys.py", title=t("nav.grain_purchases"), icon="🌾")

pages = {t("nav.pos_section"): [pos_ventas, pos_compra]}

if role == "admin":
    admin_productos = st.Page(
        "admin/products.py", title=t("nav.products"), icon="📦"
    )
    admin_inventario = st.Page(
        "admin/inventory.py", title=t("nav.inventory"), icon="📊"
    )
    admin_reportes = st.Page("admin/reports.py", title=t("nav.reports"), icon="📈")
    pages[t("nav.admin_section")] = [admin_productos, admin_inventario, admin_reportes]

pg = st.navigation(pages)
pg.run()
