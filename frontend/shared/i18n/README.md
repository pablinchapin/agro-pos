# i18n Translations

Translation data for the Streamlit frontend. Logic (`t()`, language selection)
lives in `frontend/shared/translations.py` — this directory holds data only.

## Key Naming Convention

Keys follow `entity.section.field`:

- `entity` — the domain concept (`product`, `inventory`, `report`, `auth`, `sale`, ...)
  or a shared value-set (`category`, `unit`, `role`)
- `section` — an optional grouping within the entity (`columns`, `fields`,
  `columns_products`, `columns_grains`)
- `field` — the specific label

Examples: `product.columns.name`, `report.columns_sales.total_revenue`,
`auth.login_button`.

Entries that resolve to a `dict` (e.g. `product.columns`) are meant to be used
directly with `st.dataframe`/`st.data_editor`'s `column_config` or with
`DataFrame.rename(columns=...)`. Entries that resolve to a `dict` of raw
value → translated label (e.g. `category`, `unit`, `role`) are meant to be
used for value mapping, not column renaming.

## Available Sections

| Key prefix        | Purpose                                            |
|--------------------|-----------------------------------------------------|
| `nav`              | Sidebar / navigation labels                          |
| `product`          | Product catalog page (titles, form fields, columns)  |
| `category`         | Product category value labels (seeds, fertilizers…)  |
| `unit`             | Unit of measure value labels (lb, kg, liter, unit)    |
| `person`           | Person (customer/farmer) column headers               |
| `role`             | Person/user role value labels                          |
| `inventory`        | Inventory page (titles, tabs, columns, alerts)          |
| `report`           | Reports page (titles, tabs, columns, metrics)            |
| `auth`             | Login page                                                |
| `sale`             | POS sales page                                             |
| `grain_purchase`   | POS grain purchase page                                     |
| `common`           | Generic actions/states shared across pages (save, cancel…)   |

## How to Add a New Language

1. Create `frontend/shared/i18n/<lang_code>.py` (e.g. `fr.py` for French).
2. Copy the `TRANSLATIONS` dict from `es.py` as your starting template.
3. Translate every **value** — never rename or remove a **key**.
4. Register the language in `LANGUAGES` in `frontend/shared/translations.py`:
   `"Français": "fr"`.

`t()` loads language modules via `importlib`, so no other code changes are
needed — the new language is picked up automatically.

## Rules

- Never translate keys, only values.
- Every key must exist in every language file with the same structure.
- If a key is missing from a language file, `t()` returns the raw key
  instead of crashing — check the UI for untranslated-looking strings
  (e.g. `product.columns.name` showing literally) after adding a key.
