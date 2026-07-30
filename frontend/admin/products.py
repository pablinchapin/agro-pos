import httpx
import streamlit as st

from shared.api_client import create_product, delete_product, get_products, update_product
from shared.components import show_api_error

PRODUCT_CATEGORIES = ["seeds", "fertilizers", "herbicides", "fungicides"]
PRODUCT_UNITS = ["lb", "kg", "liter", "unit"]

st.title("Catálogo de Productos")


@st.cache_data(ttl=60)
def _load_products() -> list[dict]:
    return [{**p, "price": float(p["price"])} for p in get_products()]


def _invalidate() -> None:
    _load_products.clear()


st.subheader("Nuevo producto")
with st.form("crear_producto", clear_on_submit=True):
    name = st.text_input("Nombre")
    category = st.selectbox("Categoría", options=PRODUCT_CATEGORIES)
    unit = st.selectbox("Unidad", options=PRODUCT_UNITS)
    price = st.number_input("Precio", min_value=0.01, step=0.01, format="%.2f")
    stock = st.number_input("Stock inicial", min_value=0, step=1)
    min_stock = st.number_input("Stock mínimo", min_value=0, step=1)
    submitted = st.form_submit_button("Crear producto")

if submitted:
    try:
        create_product(
            {
                "name": name,
                "category": category,
                "unit": unit,
                "price": price,
                "stock": int(stock),
                "min_stock": int(min_stock),
            }
        )
    except httpx.HTTPStatusError as e:
        show_api_error(e)
    else:
        _invalidate()
        st.success(f"Producto '{name}' creado")
        st.rerun()

st.divider()
st.subheader("Productos existentes")

products = _load_products()

if not products:
    st.info("No hay productos registrados todavía.")
else:
    edited = st.data_editor(
        products,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "created_at": st.column_config.DatetimeColumn("Creado", disabled=True),
            "name": st.column_config.TextColumn("Nombre"),
            "category": st.column_config.SelectboxColumn(
                "Categoría", options=PRODUCT_CATEGORIES
            ),
            "unit": st.column_config.SelectboxColumn("Unidad", options=PRODUCT_UNITS),
            "price": st.column_config.NumberColumn(
                "Precio", min_value=0.01, format="%.2f"
            ),
            "stock": st.column_config.NumberColumn("Stock", min_value=0),
            "min_stock": st.column_config.NumberColumn("Stock mínimo", min_value=0),
        },
        disabled=["id", "created_at"],
        hide_index=True,
        key="products_editor",
    )

    if st.button("Guardar cambios"):
        originals = {p["id"]: p for p in products}
        editable_fields = ("name", "category", "unit", "price", "stock", "min_stock")
        try:
            changed = 0
            for row in edited:
                original = originals.get(row["id"])
                if original is None:
                    continue
                diff = {
                    field: row[field]
                    for field in editable_fields
                    if row[field] != original[field]
                }
                if diff:
                    update_product(row["id"], diff)
                    changed += 1
        except httpx.HTTPStatusError as e:
            show_api_error(e)
        else:
            _invalidate()
            if changed:
                st.success(f"{changed} producto(s) actualizado(s)")
            st.rerun()

    st.divider()
    st.subheader("Eliminar producto")
    product_to_delete = st.selectbox(
        "Producto",
        options=products,
        format_func=lambda p: f"{p['name']} (ID {p['id']})",
        key="product_to_delete",
    )
    if st.button("Eliminar", type="primary"):
        try:
            delete_product(product_to_delete["id"])
        except httpx.HTTPStatusError as e:
            show_api_error(e)
        else:
            _invalidate()
            st.success("Producto eliminado")
            st.rerun()
