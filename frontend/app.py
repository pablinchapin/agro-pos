import streamlit as st

from login import login_page

if "access_token" not in st.session_state:
    login_page()
    st.stop()

role = st.session_state.get("role")

with st.sidebar:
    st.caption(f"Usuario: {st.session_state.get('username', '')} ({role})")
    if st.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

pos_ventas = st.Page("pos/sales.py", title="Ventas", icon="🛒")
pos_compra = st.Page("pos/buys.py", title="Compra de Grano", icon="🌾")

pages = {"Punto de Venta": [pos_ventas, pos_compra]}

if role == "admin":
    admin_productos = st.Page(
        "admin/products.py", title="Catálogo de Productos", icon="📦"
    )
    admin_inventario = st.Page("admin/inventory.py", title="Inventario", icon="📊")
    admin_reportes = st.Page("admin/reports.py", title="Reportes", icon="📈")
    pages["Administración"] = [admin_productos, admin_inventario, admin_reportes]

pg = st.navigation(pages)
pg.run()
