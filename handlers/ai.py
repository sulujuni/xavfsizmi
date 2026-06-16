"""
AI features powered by Groq (free llama3):
- ask_groq()       — shared helper for all AI calls
- /ask             — AI cybersecurity chat assistant
- /analyze         — AI scam message analyzer
- ai_link_verdict  — plain-language AI verdict for link checks
"""
import logging
import aiohttp

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from config import GROQ_API_KEY
from database import get_user_lang
from languages import t
from handlers.private_messages import require_subscription, react_to_message

# Conversation states
WAITING_ASK_INPUT = 30
WAITING_ANALYZE_INPUT = 31

_LANG_INSTRUCTION = {
    "uz": "Javobni faqat o'zbek tilida ber.",
    "ru": "Отвечай только на русском языке.",
    "en": "Answer only in English.",
}


# ─── Shared Groq helper ───────────────────────────────────────────────────────

async def ask_groq(system_prompt: str, user_prompt: str,
                   max_tokens: int = 500, temperature: float = 0.7) -> str:
    """
    Sends a prompt to Groq and returns the response text.
    Returns empty string on failure.
    """
    if not GROQ_API_KEY:
        return ""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=aiohttp.ClientTimeout(total=25),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    # Fallback to smaller/faster model if the big one is unavailable
                    logging.warning(f"Groq returned {resp.status}, trying fallback model")
                    return await _ask_groq_fallback(system_prompt, user_prompt, max_tokens, temperature)
    except Exception as e:
        logging.error(f"Groq error: {e}")
        return ""


async def _ask_groq_fallback(system_prompt, user_prompt, max_tokens, temperature) -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Groq fallback error: {e}")
    return ""


# ─── AI verdict for link checks ───────────────────────────────────────────────

async def ai_link_verdict(url: str, scan_data: dict, lang: str = "uz") -> str:
    """
    Generates a short plain-language verdict for a scanned URL.
    scan_data should contain: trust_score, vt_malicious, gsb_dangerous,
    domain_age, typosquat (bool).
    Returns a short verdict string or empty string.
    """
    lang_instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["en"])

    system = (
        "You are a cybersecurity assistant for everyday internet users. "
        "Explain in simple, non-technical language whether a website is safe to visit. "
        "Be concise (2-3 sentences max). " + lang_instruction
    )
    user = (
        f"Analyze this website scan result and give a short verdict for a normal user:\n"
        f"URL: {url}\n"
        f"Trust score: {scan_data.get('trust_score')}/100\n"
        f"VirusTotal threats: {scan_data.get('vt_malicious', 0)}\n"
        f"Google Safe Browsing dangerous: {scan_data.get('gsb_dangerous', False)}\n"
        f"Domain age (days): {scan_data.get('domain_age', 'unknown')}\n"
        f"Looks like a fake/lookalike domain: {scan_data.get('typosquat', False)}\n\n"
        f"Tell the user clearly: is it safe to click? What should they watch out for?"
    )
    verdict = await ask_groq(system, user, max_tokens=200, temperature=0.5)
    return verdict


# ─── /ask — AI cybersecurity chat assistant ──────────────────────────────────

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: ask for the user's question."""
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)

    # If question is provided inline (e.g. /ask how to make strong password)
    if context.args:
        question = " ".join(context.args).strip()
        await _answer_question(update, context, question, lang)
        return ConversationHandler.END

    await update.message.reply_text(t(lang, "ask_prompt"), parse_mode="Markdown")
    return WAITING_ASK_INPUT


async def ask_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: receive question and answer."""
    lang = get_user_lang(update.effective_user.id)
    question = update.message.text.strip()
    await _answer_question(update, context, question, lang)
    return ConversationHandler.END


async def _answer_question(update, context, question: str, lang: str):
    lang_instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["en"])
    status_msg = await update.message.reply_text(t(lang, "ai_thinking"))

    system = (
        "You are a friendly cybersecurity expert assistant inside a Telegram bot called "
        "'Xavfsizmi?'. You help regular users stay safe online. Answer questions about "
        "passwords, phishing, scams, malware, privacy, safe browsing, account security, etc. "
        "Keep answers practical and easy to understand. If a question is NOT about "
        "cybersecurity/online safety, politely say you only help with security topics. "
        + lang_instruction
    )
    answer = await ask_groq(system, question, max_tokens=600, temperature=0.6)

    if answer:
        await status_msg.edit_text(f"🤖 {answer}")
    else:
        await status_msg.edit_text(t(lang, "ai_unavailable"))


# ─── /analyze — AI scam message analyzer ──────────────────────────────────────

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 1: ask user to paste the suspicious message."""
    await react_to_message(update.message)
    if not await require_subscription(update, context):
        return ConversationHandler.END

    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "analyze_prompt"), parse_mode="Markdown")
    return WAITING_ANALYZE_INPUT


async def analyze_receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Step 2: receive suspicious message and analyze it."""
    lang = get_user_lang(update.effective_user.id)
    suspicious_text = update.message.text.strip()

    status_msg = await update.message.reply_text(t(lang, "ai_thinking"))

    lang_instruction = _LANG_INSTRUCTION.get(lang, _LANG_INSTRUCTION["en"])
    system = (
        "You are a scam-detection expert. A user will paste a message they received "
        "(SMS, email, Telegram, etc.). Analyze whether it is a scam, phishing, or safe. "
        "Respond in this format:\n"
        "1. Verdict: SCAM / SUSPICIOUS / LIKELY SAFE (with an emoji 🚨/⚠️/✅)\n"
        "2. Risk level: high/medium/low\n"
        "3. Red flags: list the specific warning signs you found\n"
        "4. Advice: what the user should do\n"
        "Keep it concise. " + lang_instruction
    )
    analysis = await ask_groq(system, f"Analyze this message:\n\n{suspicious_text}",
                              max_tokens=500, temperature=0.4)

    if analysis:
        await status_msg.edit_text(f"🔍 *{t(lang, 'analyze_result_title')}*\n\n{analysis}",
                                   parse_mode="Markdown")
    else:
        await status_msg.edit_text(t(lang, "ai_unavailable"))


# ─── Cancel ───────────────────────────────────────────────────────────────────

async def ai_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_user_lang(update.effective_user.id)
    await update.message.reply_text(t(lang, "breach_cancel"))
    return ConversationHandler.END
