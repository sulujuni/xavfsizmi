"""Tests for the consolidated menu command builder."""
from menu import (
    build_menu_commands,
    PUBLIC_MENU_COMMANDS,
    ADMIN_MENU_COMMANDS,
    SUPPORTED_LANGS,
)


def test_public_menu_excludes_admin_commands():
    cmds = build_menu_commands("uz", include_admin=False)
    names = {c.command for c in cmds}
    assert "start" in names
    assert "admin" not in names
    assert "broadcast" not in names


def test_admin_menu_appends_admin_commands():
    public = build_menu_commands("uz", include_admin=False)
    admin = build_menu_commands("uz", include_admin=True)
    assert len(admin) == len(public) + len(ADMIN_MENU_COMMANDS["uz"])
    names = {c.command for c in admin}
    for expected in ("admin", "broadcast", "stats", "dbinfo", "ratelimit", "addpromo"):
        assert expected in names


def test_unknown_language_falls_back_to_english():
    cmds = build_menu_commands("xx", include_admin=True)
    expected = len(PUBLIC_MENU_COMMANDS["en"]) + len(ADMIN_MENU_COMMANDS["en"])
    assert len(cmds) == expected


def test_all_supported_langs_have_same_shape():
    lengths = {lang: len(PUBLIC_MENU_COMMANDS[lang]) for lang in SUPPORTED_LANGS}
    assert len(set(lengths.values())) == 1  # all languages define the same commands
