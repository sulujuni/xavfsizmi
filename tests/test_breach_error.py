"""If the breach/dark-web check blows up, the user must see an actionable,
localized message — never the raw Python exception text."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers import breach


@pytest.mark.asyncio
async def test_unexpected_exception_does_not_leak_to_user(monkeypatch):
    async def _boom(email, lang):
        raise RuntimeError("connection to db.internal:5432 refused, secret_key=xyz123")

    monkeypatch.setattr(breach, "_check_email_full", _boom)
    monkeypatch.setattr(breach, "get_user_lang", lambda uid: "uz")
    monkeypatch.setattr(breach, "is_premium", lambda uid: True)
    monkeypatch.setattr(breach, "get_referral_credits", lambda uid: 0)
    monkeypatch.setattr(breach, "consume_referral_credit", lambda uid: None)

    status_msg = MagicMock()
    status_msg.edit_text = AsyncMock()

    update = MagicMock()
    update.effective_user.id = 111
    update.message.text = "someone@example.com"
    update.effective_chat.id = 222
    update.message.delete = AsyncMock()

    context = MagicMock()
    context.bot.send_message = AsyncMock(return_value=status_msg)

    await breach.breach_receive_input(update, context)

    shown_text = status_msg.edit_text.call_args.args[0]
    assert "secret_key" not in shown_text
    assert "db.internal" not in shown_text
    assert "RuntimeError" not in shown_text
    assert "urinib ko'ring" in shown_text  # actionable, not a dead end
