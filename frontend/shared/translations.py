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
