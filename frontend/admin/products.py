import httpx
import streamlit as st

from shared.api_client import (
    activate_product,
    create_product,
    deactivate_product,
    get_inactive_products,
    get_products,
    update_product,
)
from shared.components import show_api_error
from shared.translations import t

PRODUCT_CATEGORIES = ["seeds", "fertilizers", "herbicides", "fungicides"]
PRODUCT_UNITS = ["lb", "kg", "liter", "unit"]

st.title(t("product.title"))


@st.cache_data(ttl=60)
def _load_products() -> list[dict]:
    return [{**p, "price": float(p["price"])} for p in get_products()]


@st.cache_data(ttl=60)
def _load_inactive_products() -> list[dict]:
    return [{**p, "price": float(p["price"])} for p in get_inactive_products()]


def _invalidate() -> None:
    _load_products.clear()
    _load_inactive_products.clear()


@st.dialog(t("product.confirm_deactivate_title"))
def confirm_deactivate(selected_products: list[dict]) -> None:
    st.write(t("product.confirm_deactivate_msg").format(count=len(selected_products)))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("common.confirm"), type="primary", key="confirm_deactivate_yes"):
            for p in selected_products:
                try:
                    deactivate_product(p["id"])
                except httpx.HTTPStatusError as e:
                    try:
                        detail = e.response.json().get("detail", "")
                    except ValueError:
                        detail = ""
                    st.error(t("product.deactivate_error").format(name=p["name"], detail=detail))
                else:
                    st.success(t("product.deactivate_success").format(name=p["name"]))
            _invalidate()
            st.rerun()
    with col2:
        if st.button(t("common.cancel"), key="confirm_deactivate_no"):
            st.rerun()


@st.dialog(t("product.confirm_activate_title"))
def confirm_activate(selected_products: list[dict]) -> None:
    st.write(t("product.confirm_activate_msg").format(count=len(selected_products)))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t("common.confirm"), type="primary", key="confirm_activate_yes"):
            for p in selected_products:
                try:
                    activate_product(p["id"])
                except httpx.HTTPStatusError as e:
                    try:
                        detail = e.response.json().get("detail", "")
                    except ValueError:
                        detail = ""
                    st.error(t("product.activate_error").format(name=p["name"], detail=detail))
                else:
                    st.success(t("product.activate_success").format(name=p["name"]))
            _invalidate()
            st.rerun()
    with col2:
        if st.button(t("common.cancel"), key="confirm_activate_no"):
            st.rerun()


if "show_create_form" not in st.session_state:
    st.session_state.show_create_form = False

if st.button(t("product.add_new")):
    st.session_state.show_create_form = not st.session_state.show_create_form

if st.session_state.show_create_form:
    with st.container():
        st.subheader(t("product.new"))
        with st.form("crear_producto", clear_on_submit=True):
            name = st.text_input(t("product.fields.name"))
            category = st.selectbox(
                t("product.fields.category"),
                options=PRODUCT_CATEGORIES,
                format_func=lambda c: t("category").get(c, c),
            )
            unit = st.selectbox(
                t("product.fields.unit"),
                options=PRODUCT_UNITS,
                format_func=lambda u: t("unit").get(u, u),
            )
            price = st.number_input(
                t("product.fields.price"), min_value=0.00, step=0.01, format="%.2f"
            )
            stock = st.number_input(t("product.fields.initial_stock"), min_value=0, step=1)
            min_stock = st.number_input(t("product.fields.min_stock"), min_value=0, step=1)
            submitted = st.form_submit_button(t("product.create"))

        if st.button(t("product.cancel")):
            st.session_state.show_create_form = False
            st.rerun()

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
                st.session_state.show_create_form = False
                st.success(t("product.created_success").format(name=name))
                st.rerun()

st.divider()
st.subheader(t("product.existing"))

products = _load_products()

if not products:
    st.info(t("product.none_yet"))
else:
    category_labels = t("category")
    category_labels_rev = {v: k for k, v in category_labels.items()}
    unit_labels = t("unit")
    unit_labels_rev = {v: k for k, v in unit_labels.items()}
    status_active = t("product.status_active")
    status_inactive = t("product.status_inactive")

    editable_fields = ("name", "category", "unit", "price", "stock", "min_stock")
    display_products = [
        {
            "_selected": False,
            "name": p["name"],
            "category": category_labels.get(p["category"], p["category"]),
            "unit": unit_labels.get(p["unit"], p["unit"]),
            "price": p["price"],
            "stock": p["stock"],
            "min_stock": p["min_stock"],
            "status": status_active if p["is_active"] else status_inactive,
        }
        for p in products
    ]

    columns = t("product.columns")
    edited = st.data_editor(
        display_products,
        column_config={
            "_selected": st.column_config.CheckboxColumn(
                t("product.select"), width="small", default=False
            ),
            "name": st.column_config.TextColumn(columns["name"], width="large"),
            "category": st.column_config.SelectboxColumn(
                columns["category"],
                options=list(category_labels.values()),
                width="medium",
            ),
            "unit": st.column_config.SelectboxColumn(
                columns["unit"], options=list(unit_labels.values()), width="medium"
            ),
            "price": st.column_config.NumberColumn(
                columns["price"], min_value=0.00, format="Q%.2f", width="small"
            ),
            "stock": st.column_config.NumberColumn(
                columns["stock"], min_value=0, width="small"
            ),
            "min_stock": st.column_config.NumberColumn(
                columns["min_stock"], min_value=0, width="small"
            ),
            "status": st.column_config.TextColumn(
                columns["status"], disabled=True, width="small"
            ),
        },
        width="stretch",
        num_rows="fixed",
        hide_index=True,
        key="products_editor",
    )

    if st.button(t("product.save")):
        try:
            changed = 0
            for original, row in zip(products, edited):
                diff = {}
                for field in editable_fields:
                    value = row[field]
                    if field == "category":
                        value = category_labels_rev.get(value, value)
                    elif field == "unit":
                        value = unit_labels_rev.get(value, value)
                    if value != original[field]:
                        diff[field] = value
                if diff:
                    update_product(original["id"], diff)
                    changed += 1
        except httpx.HTTPStatusError as e:
            show_api_error(e)
        else:
            _invalidate()
            if changed:
                st.success(t("product.updated_success").format(count=changed))
            st.rerun()

    st.divider()

    selected_products = [
        original for original, row in zip(products, edited) if row.get("_selected")
    ]

    if not selected_products:
        st.caption(t("product.none_selected"))

    if st.button(
        t("product.deactivate_selected"),
        type="primary",
        disabled=not selected_products,
    ):
        confirm_deactivate(selected_products)

st.divider()
with st.expander(t("product.inactive_section"), expanded=False):
    inactive_products = _load_inactive_products()

    if not inactive_products:
        st.info(t("product.none_yet"))
    else:
        category_labels = t("category")
        unit_labels = t("unit")

        display_inactive = [
            {
                "_selected": False,
                "name": p["name"],
                "category": category_labels.get(p["category"], p["category"]),
                "unit": unit_labels.get(p["unit"], p["unit"]),
                "price": p["price"],
                "stock": p["stock"],
                "min_stock": p["min_stock"],
            }
            for p in inactive_products
        ]

        columns = t("product.columns")
        edited_inactive = st.data_editor(
            display_inactive,
            column_config={
                "_selected": st.column_config.CheckboxColumn(
                    t("product.select"), default=False
                ),
                "name": st.column_config.TextColumn(columns["name"]),
                "category": st.column_config.TextColumn(columns["category"]),
                "unit": st.column_config.TextColumn(columns["unit"]),
                "price": st.column_config.NumberColumn(columns["price"], format="%.2f"),
                "stock": st.column_config.NumberColumn(columns["stock"]),
                "min_stock": st.column_config.NumberColumn(columns["min_stock"]),
            },
            disabled=["name", "category", "unit", "price", "stock", "min_stock"],
            width="stretch",
            num_rows="fixed",
            hide_index=True,
            key="inactive_products_editor",
        )

        selected_inactive = [
            original
            for original, row in zip(inactive_products, edited_inactive)
            if row.get("_selected")
        ]

        if not selected_inactive:
            st.caption(t("product.none_selected"))

        if st.button(
            t("product.activate_selected"),
            type="primary",
            disabled=not selected_inactive,
        ):
            confirm_activate(selected_inactive)
