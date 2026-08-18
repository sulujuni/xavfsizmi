"""Which messages count as a link.

The bot replied with the /start welcome text whenever the message did not match
URL_REGEX, and the regex required http(s):// or www. — so a bare domain, the
form phishing links are actually pasted in, produced a welcome message.
"""
import pytest

from bot.handlers.scan import URL_REGEX, normalize_url


@pytest.mark.parametrize("text, expected", [
    ("https://google.com", "https://google.com"),
    ("http://google.com", "http://google.com"),
    ("www.google.com", "https://www.google.com"),
    # Bare domains — the case that used to fall through to the welcome message.
    ("google.com", "https://google.com"),
    ("uzcard-bonus.top", "https://uzcard-bonus.top"),
    ("example.uz", "https://example.uz"),
    ("t.me/abc", "https://t.me/abc"),
    # Embedded in a sentence, and with a path/query.
    ("shu havolani ko'r: firibgar.top/win", "https://firibgar.top/win"),
    ("https://uzum-cashback.ru/win?id=8842", "https://uzum-cashback.ru/win?id=8842"),
])
def test_link_is_detected_and_normalized(text, expected):
    match = URL_REGEX.search(text)
    assert match is not None, f"not detected: {text}"
    assert normalize_url(match.group(0)) == expected


def test_uppercase_scheme_is_detected():
    assert URL_REGEX.search("HTTPS://GOOGLE.COM") is not None


@pytest.mark.parametrize("text", [
    "salom qalaysan",
    "rahmat.men yozdim",     # looks like a domain, .men is not a TLD we accept
    "1.5 kg",
    "narx 20.000 so'm",
    "a.b",
])
def test_plain_text_is_not_treated_as_a_link(text):
    assert URL_REGEX.search(text) is None, f"falsely detected: {text}"


def test_normalize_leaves_an_existing_scheme_alone():
    assert normalize_url("http://x.uz") == "http://x.uz"
    assert normalize_url("x.uz") == "https://x.uz"
