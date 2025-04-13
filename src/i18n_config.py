from pathlib import Path

import i18n


def setup_i18n():
    base_dir = Path(__file__).parent.parent.absolute()
    locales_path = base_dir / "resources" / "locales"

    i18n.load_path.append(str(locales_path))
    i18n.set("filename_format", "{locale}.{format}")
    i18n.set("file_format", "yml")
    i18n.set("locale", "en")
    i18n.set("fallback", "en")
    i18n.set("enable_memoization", True)


def change_language(lang_code):
    """Changes the current language.

    Args:
        lang_code (str): Language code ('en' or 'es')
    """
    if lang_code in ["en", "es"]:
        i18n.set("locale", lang_code)
        return True
    return False


def get_current_language():
    """Returns the current language code.

    Returns:
        str: Current language code
    """
    return i18n.get("locale")
