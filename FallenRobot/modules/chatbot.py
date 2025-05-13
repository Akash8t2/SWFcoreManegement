import html
import json
import re
import unicodedata
import string
from time import sleep

import requests
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    Update,
    User,
    ChatAction,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

import FallenRobot.modules.sql.chatbot_sql as sql
from FallenRobot import BOT_ID, BOT_NAME, BOT_USERNAME, dispatcher
from FallenRobot.modules.helper_funcs.chat_status import user_admin, user_admin_no_reply
from FallenRobot.modules.log_channel import gloggable

GEMINI_API_KEY = "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"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


def extract_clean_name(raw_name):
    normalized = unicodedata.normalize('NFKD', raw_name)
    clean = ''.join(ch for ch in normalized if ch.isalnum() or ch.isspace())
    words = clean.split()
    if words:
        return words[0].capitalize()
    return "Unknown"


@run_async
@user_admin_no_reply
@gloggable
def fallenrm(update: Update, context: CallbackContext) -> str:
    query: CallbackQuery = update.callback_query
    user: User = update.effective_user
    match = re.match(r"rm_chat(\d+)", query.data)
    if match:
        user_id = match.group(1)
        chat: Chat = update.effective_chat
        if sql.set_fallen(chat.id):
            sql.set_fallen(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_DISABLED\n"
                f"<b>Admin :</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                f"{dispatcher.bot.first_name} ᴄʜᴀᴛʙᴏᴛ ᴅɪsᴀʙʟᴇᴅ ʙʏ {mention_html(user.id, user.first_name)}.",
                parse_mode=ParseMode.HTML,
            )
    return ""


@run_async
@user_admin_no_reply
@gloggable
def fallenadd(update: Update, context: CallbackContext) -> str:
    query: CallbackQuery = update.callback_query
    user: User = update.effective_user
    match = re.match(r"add_chat(\d+)", query.data)
    if match:
        user_id = match.group(1)
        chat: Chat = update.effective_chat
        if sql.rem_fallen(chat.id):
            sql.rem_fallen(user_id)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_ENABLED\n"
                f"<b>Admin :</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
        else:
            update.effective_message.edit_text(
                f"{dispatcher.bot.first_name} ᴄʜᴀᴛʙᴏᴛ ᴇɴᴀʙʟᴇᴅ ʙʏ {mention_html(user.id, user.first_name)}.",
                parse_mode=ParseMode.HTML,
            )
    return ""


@run_async
@user_admin
@gloggable
def fallen(update: Update, context: CallbackContext):
    message = update.effective_message
    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton(text="✅ Enable", callback_data=f"add_chat{message.chat_id}"),
            InlineKeyboardButton(text="❌ Disable", callback_data=f"rm_chat{message.chat_id}"),
        ]]
    )
    message.reply_text(
        text="• ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴩᴛɪᴏɴ ᴛᴏ ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML,
    )


def fallen_message(context: CallbackContext, message):
    reply_message = message.reply_to_message
    if message.text.lower() == "fallen":
        return True
    elif BOT_USERNAME in message.text.upper():
        return True
    elif reply_message and reply_message.from_user.id == BOT_ID:
        return True
    return False


def chatbot(update: Update, context: CallbackContext):
    message = update.effective_message
    chat_id = update.effective_chat.id
    bot = context.bot
    is_fallen = sql.is_fallen(chat_id)
    if is_fallen:
        return

    if message.text and not message.document:
        if re.search(r"(mera|meri).*(naam|name)", message.text.lower()):
            raw_name = message.from_user.full_name or message.from_user.username or ""
            probable_name = extract_clean_name(raw_name)
            message.reply_text(f"ᴀᴀᴩᴋᴀ ɴᴀᴀᴍ {probable_name} ʜᴏ sᴀᴋᴛᴀ ʜᴀɪ.")
            return

        if not fallen_message(context, message):
            return

        bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        prompt = message.text
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        try:
            response = requests.post(
                GEMINI_API_URL,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )
            data = response.json()
            reply = (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text")
            )
            if reply:
                sleep(0.5)
                message.reply_text(reply)
            else:
                message.reply_text("No response from Gemini AI.")
        except Exception:
            message.reply_text("Chatbot error: Could not connect to Gemini API.")


__help__ = f"""
*{BOT_NAME} has a chatbot powered by Gemini AI:*

» /chatbot : Enable/disable chatbot replies in group.
"""

__mod_name__ = "Cʜᴀᴛʙᴏᴛ"

CHATBOTK_HANDLER = CommandHandler("chatbot", fallen)
ADD_CHAT_HANDLER = CallbackQueryHandler(fallenadd, pattern=r"add_chat\d+")
RM_CHAT_HANDLER = CallbackQueryHandler(fallenrm, pattern=r"rm_chat\d+")
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!") & ~Filters.regex(r"^/")),
    chatbot,
)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(CHATBOTK_HANDLER)
dispatcher.add_handler(RM_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    CHATBOTK_HANDLER,
    RM_CHAT_HANDLER,
    CHATBOT_HANDLER,
]
