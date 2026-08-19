---
name: frontend-i18n
description: Use this skill when adding translations, a language selector, or new languages to the frontend. Covers how to use t(), where translation files live, and how to add a new language. Never add translation content to this skill — it lives in frontend/shared/i18n/*.py.
---

## File Structure

frontend/shared/
i18n/
init.py
es.py ← Spanish translations (datos, not logic)
en.py ← English translations (datos, not logic)
README.md ← key naming conventions + how to add a new language
translations.py ← t() function + language management (logic only)


## translations.py — Logic Only

```python
import streamlit as st
from importlib import import_module

LANGUAGES = {
    "Español": "es",
    "English": "en",
}

def get_language() -> str:
    return st.session_state.get("language", "es")

def t(key: str) -> any:
    lang = get_language()
    try:
        module = import_module(f"shared.i18n.{lang}")
    except ModuleNotFoundError:
        module = import_module("shared.i18n.es")
    translations = module.TRANSLATIONS
    keys = key.split(".")
    result = translations
    for k in keys:
        if isinstance(result, dict):
            result = result.get(k, key)
        else:
            return key
    return result
```

Using `importlib.import_module` means adding a new language never 
requires modifying translations.py — just add the file and register 
the language in LANGUAGES.

## Language Selector — app.py sidebar

```python
from shared.translations import LANGUAGES, get_language

selected_label = next(
    k for k, v in LANGUAGES.items() if v == get_language()
)
lang_choice = st.sidebar.selectbox(
    "🌐 Language / Idioma",
    options=list(LANGUAGES.keys()),
    index=list(LANGUAGES.keys()).index(selected_label)
)
st.session_state.language = LANGUAGES[lang_choice]
```

## Using t() in Pages

```python
from shared.translations import t

# Simple string
st.title(t("product.title"))

# Column rename — works when key points to a dict
df = df.rename(columns=t("product.columns"))

# Drop unwanted columns before rename
df = df.drop(columns=["id", "created_at"], errors="ignore")

# Value translation (categories, roles)
df["category"] = df["category"].map(
    lambda x: t("category").get(x, x)
)

# String interpolation
st.warning(t("inventory.low_stock_alert").format(count=n))
```

## Adding a New Language

1. Create `frontend/shared/i18n/<lang_code>.py`
2. Copy `TRANSLATIONS` dict from `es.py` as the starting template
3. Translate all values — never translate keys
4. Register in `translations.py` LANGUAGES dict:
   `"Français": "fr"`
5. That's it — `t()` picks it up automatically via importlib

Read `frontend/shared/i18n/README.md` for key naming conventions 
and the full inventory of available sections.

## Rules
- Never hardcode Spanish or English strings in page files — always use t()
- Never add translation dictionaries to this skill — they live in i18n/*.py
- Never translate keys — only values
- t() returns the key itself if not found — missing translations are 
  visible without crashing
- When adding a key: always add it to ALL language files simultaneously
- Column rename pattern only works when the key resolves to a dict —
  verify with t("product.columns") before using in df.rename()