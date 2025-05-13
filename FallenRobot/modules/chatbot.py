import html
import re
import os
import unicodedata
from time import sleep
import google.generativeai as genai
from telegram import (
    CallbackQuery, Chat, InlineKeyboardButton,
    InlineKeyboardMarkup, ParseMode, Update,
    User, ChatAction
)
from telegram.ext import (
    CallbackContext, CallbackQueryHandler,
    CommandHandler, Filters, MessageHandler, run_async
)
from telegram.utils.helpers import mention_html

import FallenRobot.modules.sql.chatbot_sql as sql
from FallenRobot import BOT_ID, BOT_NAME, BOT_USERNAME, dispatcher
from FallenRobot.modules.helper_funcs.chat_status import user_admin, user_admin_no_reply
from FallenRobot.modules.log_channel import gloggable
from FallenRobot.modules.sql import chat_context

# Secure API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # .env file से
genai.configure(api_key=GEMINI_API_KEY)

# Model Configuration
generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 1024,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    generation_config=generation_config,
    safety_settings=safety_settings
)

def extract_clean_name(raw_name):
    """नाम को साफ करने का फंक्शन"""
    normalized = unicodedata.normalize('NFKD', raw_name)
    clean = ''.join([ch for ch in normalized if ch.isalnum() or ch.isspace()])
    words = clean.split()
    return words[0].capitalize() if words else "Unknown"

@run_async
@user_admin_no_reply
@gloggable
def fallenrm(update: Update, context: CallbackContext) -> str:
    """चैटबॉट डिसेबल करने का हैंडलर"""
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"rm_chat(\d+)", query.data)
    
    if match:
        user_id = match.group(1)
        chat = update.effective_chat
        
        if sql.set_fallen(chat.id):
            sql.set_fallen(user_id)
            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_DISABLED\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
            return log_message
            
        query.edit_message_text(
            f"{dispatcher.bot.first_name} चैटबॉट डिसेबल किया गया {mention_html(user.id, user.first_name)} द्वारा।",
            parse_mode=ParseMode.HTML
        )
    return ""

@run_async
@user_admin_no_reply
@gloggable
def fallenadd(update: Update, context: CallbackContext) -> str:
    """चैटबॉट एक्टिवेट करने का हैंडलर"""
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"add_chat(\d+)", query.data)
    
    if match:
        user_id = match.group(1)
        chat = update.effective_chat
        
        if sql.rem_fallen(chat.id):
            sql.rem_fallen(user_id)
            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"AI_ENABLED\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            )
            return log_message
            
        query.edit_message_text(
            f"{dispatcher.bot.first_name} चैटबॉट एक्टिवेट किया गया {mention_html(user.id, user.first_name)} द्वारा।",
            parse_mode=ParseMode.HTML
        )
    return ""

@run_async
@user_admin
@gloggable
def fallen(update: Update, context: CallbackContext):
    """एडमिन कंट्रोल पैनल"""
    message = update.effective_message
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ एक्टिवेट", callback_data=f"add_chat{message.chat_id}"),
        InlineKeyboardButton("❌ डिसेबल", callback_data=f"rm_chat{message.chat_id}")
    ]])
    message.reply_text(
        "• चैटबॉट सेटिंग्स चुनें:",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

def fallen_message(context: CallbackContext, message):
    """मैसेज ट्रिगर चेक करें"""
    return any([
        message.text.lower() == "fallen",
        BOT_USERNAME in message.text.upper(),
        message.reply_to_message and 
        message.reply_to_message.from_user.id == BOT_ID
    ])

def chatbot(update: Update, context: CallbackContext):
    """मुख्य चैटबॉट लॉजिक"""
    message = update.effective_message
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if sql.is_fallen(chat_id):
        return

    if message.text and not message.document:
        # नाम डिटेक्शन लॉजिक
        if re.search(r"(mera|meri).*(naam|name)", message.text.lower()):
            raw_name = message.from_user.full_name or message.from_user.username or ""
            probable_name = extract_clean_name(raw_name)
            message.reply_text(f"आपका नाम {probable_name} हो सकता है।")
            return

        if not fallen_message(context, message):
            return

        # कॉन्टेक्स्ट मैनेजमेंट
        prompt = message.text
        previous = chat_context.get_context(user_id)
        full_prompt = f"{previous}\nUser: {prompt}" if previous else prompt

        context.bot.send_chat_action(chat_id, ChatAction.TYPING)

        try:
            # Gemini AI को कॉल करें
            response = model.generate_content(full_prompt)
            reply = response.text
            
            if reply:
                sleep(0.5)  # Natural feel के लिए
                message.reply_text(reply)
                chat_context.set_context(user_id, f"{full_prompt}\nBot: {reply}")
            else:
                message.reply_text("⚠️ कोई उपयुक्त जवाब नहीं मिला")

        except genai.types.StopCandidateException as e:
            message.reply_text("🚫 सुरक्षा नीतियों के कारण यह प्रश्न अस्वीकृत")
        
        except Exception as e:
            error_msg = f"त्रुटि: {str(e)}"
            if "API_KEY" in str(e):
                error_msg = "🔑 अमान्य API कॉन्फ़िगरेशन"
            message.reply_text(error_msg)

def reset_chat(update: Update, context: CallbackContext):
    """चैट हिस्ट्री रीसेट करें"""
    user_id = update.effective_user.id
    chat_context.clear_context(user_id)
    update.message.reply_text("✅ चैट इतिहास सफलतापूर्वक रीसेट हो गया!")

__help__ = f"""
*{BOT_NAME} Google Gemini AI द्वारा संचालित:*

» /chatbot - चैटबॉट सक्रिय/निष्क्रिय करें
» /resetchat - वार्तालाप इतिहास रीसेट करें
"""

__mod_name__ = "𝗚𝗘𝗠𝗜𝗡𝗜 𝗔𝗜"

# हैंडलर सेटअप
CHATBOTK_HANDLER = CommandHandler("chatbot", fallen)
ADD_CHAT_HANDLER = CallbackQueryHandler(fallenadd, pattern=r"add_chat\d+")
RM_CHAT_HANDLER = CallbackQueryHandler(fallenrm, pattern=r"rm_chat\d+")
CHATBOT_HANDLER = MessageHandler(
    Filters.text & ~Filters.command & ~Filters.regex(r"^[!#]"),
    chatbot
)
RESET_CONTEXT_HANDLER = CommandHandler("resetchat", reset_chat)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(CHATBOTK_HANDLER)
dispatcher.add_handler(RM_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(RESET_CONTEXT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    CHATBOTK_HANDLER,
    RM_CHAT_HANDLER,
    CHATBOT_HANDLER,
    RESET_CONTEXT_HANDLER,
]
