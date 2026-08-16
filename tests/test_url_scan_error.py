"""If the URL scan pipeline blows up, the user must see a localized, actionable
message — not a hardcoded Uzbek-only string regardless of their chosen language.

Found live: user 6601567684 hit this exact path on 2026-08-07 (events table,
error_shown/url_scan_error existed in the event schema but the message itself
was still `await status_msg.edit_text("❌ Havolani tahlil qilish jarayonida
xatolik yuz berdi.")` — hardcoded, no t(lang, ...) call at all."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers import scan


@pytest.mark.asyncio
async def test_url_scan_exception_shows_localized_actionable_message(monkeypatch):
    async def _boom(url):
        raise RuntimeError("connection to vt-proxy.internal:9443 refused")

    monkeypatch.setattr(scan, "check_virustotal", _boom)
    monkeypatch.setattr(scan, "get_user_lang", lambda uid: "ru")
    monkeypatch.setattr(scan, "require_subscription", AsyncMock(return_value=True))
    monkeypatch.setattr(scan, "check_and_consume_limit", lambda uid: True)
    monkeypatch.setattr(scan, "react_to_message", AsyncMock())

    status_msg = MagicMock()
    status_msg.edit_text = AsyncMock()

    update = MagicMock()
    update.effective_user.id = 6601567684
    update.message.text = "https://example.com"
    update.message.reply_text = AsyncMock(return_value=status_msg)

    context = MagicMock()

    await scan.handle_private_message(update, context)

    shown_text = status_msg.edit_text.call_args.args[0]
    assert shown_text == "❌ Ошибка при анализе ссылки. Попробуйте позже."
    assert "RuntimeError" not in shown_text
    assert "vt-proxy.internal" not in shown_text
