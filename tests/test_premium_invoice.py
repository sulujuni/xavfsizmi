"""The Telegram Stars invoice sheet must be localized — it was hardcoded to
English regardless of the user's chosen language."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from bot.handlers import premium


@pytest.mark.asyncio
async def test_personal_invoice_localized_for_russian(monkeypatch):
    monkeypatch.setattr(premium, "get_user_lang", lambda uid: "ru")
    context = MagicMock()
    context.bot.send_invoice = AsyncMock()

    query = MagicMock()
    query.data = "pay_p1m_stars"
    query.message.chat_id = 555
    query.from_user.id = 111
    query.answer = AsyncMock()

    update = MagicMock()
    update.callback_query = query

    await premium.payment_gateway_callback(update, context)

    _, kwargs = context.bot.send_invoice.call_args
    assert kwargs["title"] == "Личный Премиум"
    assert "дней" in kwargs["description"]
    assert "Premium" not in kwargs["title"] or kwargs["title"] == "Личный Премиум"


@pytest.mark.asyncio
async def test_group_invoice_localized_for_uzbek(monkeypatch):
    monkeypatch.setattr(premium, "get_user_lang", lambda uid: "uz")
    context = MagicMock()
    context.bot.send_invoice = AsyncMock()

    query = MagicMock()
    query.data = "pay_g1m_stars"
    query.message.chat_id = 555
    query.from_user.id = 111
    query.answer = AsyncMock()

    update = MagicMock()
    update.callback_query = query

    await premium.payment_gateway_callback(update, context)

    _, kwargs = context.bot.send_invoice.call_args
    assert kwargs["title"] == "Guruh Premium"
    assert "kunlik" in kwargs["description"]
