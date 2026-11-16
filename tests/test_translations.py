import pytest

from translations import CROP_NAMES, TRANSLATIONS, get_text_direction, t, translate_crop

LANGS = ["en", "fr", "ar"]


def test_all_languages_present():
    assert set(LANGS) <= set(TRANSLATIONS)


@pytest.mark.parametrize("lang", ["fr", "ar"])
def test_every_english_key_is_translated(lang):
    missing = set(TRANSLATIONS["en"]) - set(TRANSLATIONS[lang])
    assert not missing, f"{lang} is missing keys: {sorted(missing)}"


def test_t_falls_back_to_english_then_key():
    assert t("app_title", "xx") == TRANSLATIONS["en"]["app_title"]
    assert t("definitely_not_a_key", "fr") == "definitely_not_a_key"


def test_text_direction():
    assert get_text_direction("ar") == "rtl"
    assert get_text_direction("en") == "ltr"
    assert get_text_direction("fr") == "ltr"


@pytest.mark.parametrize("crop", sorted(CROP_NAMES))
def test_every_crop_has_all_languages(crop):
    assert all(CROP_NAMES[crop].get(lang) for lang in LANGS)


def test_translate_crop_normalises_and_falls_back():
    assert translate_crop("  Rice ", "fr") == "Riz"
    assert translate_crop("quinoa", "fr") == "Quinoa"
