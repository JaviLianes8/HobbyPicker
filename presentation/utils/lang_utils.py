import locale


def get_system_language() -> str:
    """Return 'es' for Spanish locales and 'en' otherwise."""
    sys_lang = locale.getdefaultlocale()[0] or "en"
    return "es" if sys_lang.lower().startswith("es") else "en"

