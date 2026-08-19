from datetime import date

import httpx
import pandas as pd
import streamlit as st

from shared.api_client import create_sale, get_persons_by_role, get_products
from shared.components import show_api_error
from shared.translations import t

st.title(t("sale.title"))

if "cart" not in st.session_state:
    st.session_state.cart = []
if "sale_customer_id" not in st.session_state:
    st.session_state.sale_customer_id = None
if "sale_qty" not in st.session_state:
    st.session_state.sale_qty = 1
if "sale_product_id" not in st.session_state:
    st.session_state.sale_product_id = None


@st.cache_data(ttl=60)
def _load_customers() -> list[dict]:
    return get_persons_by_role("customer")


@st.cache_data(ttl=60)
def _load_products() -> list[dict]:
    return [{**p, "price": float(p["price"])} for p in get_products()]


customers = _load_customers()

if not customers:
    st.warning(t("sale.no_customer"))
    st.session_state.sale_customer_id = None
else:
    customer = st.selectbox(
        t("sale.select_customer"),
        options=customers,
        format_func=lambda p: f"{p['full_name']} ({p['phone'] or '-'})",
    )
    st.session_state.sale_customer_id = customer["id"]

st.divider()

products = _load_products()

if not products:
    st.info(t("sale.no_products"))
else:
    col1, col2 = st.columns([3, 1])
    with col1:
        product = st.selectbox(
            t("sale.select_product"),
            options=products,
            format_func=lambda p: (
                f"{p['name']} - Q{p['price']:.2f} "
                f"({t('sale.available').format(stock=p['stock'])})"
            ),
        )

    if product["id"] != st.session_state.sale_product_id:
        st.session_state.sale_product_id = product["id"]
        st.session_state.pop("sale_qty", None)
        st.rerun()

    with col2:
        quantity = st.number_input(
            t("sale.quantity"),
            min_value=1,
            max_value=max(product["stock"], 1),
            step=1,
            key="sale_qty",
        )

    if st.button(t("sale.add_to_cart"), disabled=product["stock"] < 1):
        existing = next(
            (
                i
                for i, item in enumerate(st.session_state.cart)
                if item["product_id"] == product["id"]
            ),
            None,
        )
        if existing is not None:
            current_qty = st.session_state.cart[existing]["quantity"]
            new_qty = min(current_qty + quantity, product["stock"])
            if new_qty < current_qty + quantity:
                st.warning(t("sale.stock_capped"))
            st.session_state.cart[existing]["quantity"] = new_qty
            st.session_state.cart[existing]["subtotal"] = (
                new_qty * st.session_state.cart[existing]["unit_price"]
            )
        else:
            st.session_state.cart.append(
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": quantity,
                    "unit_price": product["price"],
                    "subtotal": quantity * product["price"],
                    "stock": product["stock"],
                }
            )
        st.session_state.pop("sale_qty", None)
        st.rerun()

st.divider()
st.subheader(t("sale.cart"))

if not st.session_state.cart:
    st.info(t("sale.cart_empty_msg"))
else:
    columns = t("sale.columns")
    cart_df = pd.DataFrame(
        [
            {
                "_remove": False,
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "unit_price": item["unit_price"],
                "subtotal": item["subtotal"],
            }
            for item in st.session_state.cart
        ]
    )

    edited_df = st.data_editor(
        cart_df,
        column_config={
            "_remove": st.column_config.CheckboxColumn(
                t("sale.columns.remove"), default=False
            ),
            "product_name": st.column_config.TextColumn(
                columns["product"], disabled=True
            ),
            "quantity": st.column_config.NumberColumn(
                columns["quantity"],
                min_value=1,
                max_value=None,  # Streamlit doesn't enforce per-row max in data_editor
                step=1,
                format="%d",
            ),
            "unit_price": st.column_config.NumberColumn(
                columns["unit_price"], format="Q%.2f", disabled=True
            ),
            "subtotal": st.column_config.NumberColumn(
                columns["subtotal"], format="Q%.2f", disabled=True
            ),
        },
        num_rows="fixed",
        hide_index=True,
        width="stretch",
        key="cart_editor",
    )

    stock_capped = False
    for i, row in enumerate(edited_df.itertuples()):
        max_stock = st.session_state.cart[i]["stock"]
        qty = min(int(row.quantity), max_stock)
        if qty != int(row.quantity):
            stock_capped = True
        st.session_state.cart[i]["quantity"] = qty
        st.session_state.cart[i]["subtotal"] = (
            qty * st.session_state.cart[i]["unit_price"]
        )

    if stock_capped:
        st.warning(t("sale.stock_capped"))

    total = sum(item["subtotal"] for item in st.session_state.cart)
    st.metric(t("sale.total"), f"Q{total:.2f}")

    selected_for_removal = [
        i for i, removed in enumerate(edited_df["_remove"]) if removed
    ]

    col_remove, col_clear = st.columns(2)
    with col_remove:
        if st.button(
            t("sale.remove_selected"),
            disabled=not selected_for_removal,
        ):
            st.session_state.cart = [
                item
                for i, item in enumerate(st.session_state.cart)
                if i not in selected_for_removal
            ]
            st.rerun()
    with col_clear:
        if st.button(t("sale.clear_cart")):
            st.session_state.cart = []
            st.rerun()

st.divider()

no_customer = st.session_state.sale_customer_id is None
cart_empty = not st.session_state.cart

if no_customer:
    st.caption(t("sale.no_customer"))
elif cart_empty:
    st.caption(t("sale.cart_empty_msg"))

if st.button(
    t("sale.confirm_sale"),
    type="primary",
    disabled=no_customer or cart_empty,
):
    payload = {
        "person_id": st.session_state.sale_customer_id,
        "date": date.today().isoformat(),
        "items": [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price": str(item["unit_price"]),
            }
            for item in st.session_state.cart
        ],
    }
    try:
        create_sale(payload)
    except httpx.HTTPStatusError as e:
        show_api_error(e)
    else:
        st.success(t("sale.sale_success"))
        st.session_state.cart = []
        st.session_state.sale_customer_id = None
        st.cache_data.clear()
        st.rerun()
