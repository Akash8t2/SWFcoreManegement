import importlib
import re
import time
from platform import python_version as y
from sys import argv

from pyrogram import __version__ as pyrover
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram import __version__ as telever
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown
from telethon import __version__ as tlhver

import FallenRobot.modules.sql.users_sql as sql
from FallenRobot import (
    BOT_NAME,
    BOT_USERNAME,
    LOGGER,
    OWNER_ID,
    START_IMG,
    SUPPORT_CHAT,
    TOKEN,
    StartTime,
    dispatcher,
    pbot,
    telethn,
    updater,
)
from FallenRobot.modules import ALL_MODULES
from FallenRobot.modules.helper_funcs.chat_status import is_user_admin
from FallenRobot.modules.helper_funcs.misc import paginate_modules


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """
*Êœá´‡Ê* {}, ðŸ¥€

*à¹ á´›ÊœÉªs Éªs* {} !
âž»ð— ð—˜ ð—Ÿð—”ð——ð—žð—œ ð—žð—œ ð—Ÿð—¢ð—¬ð—˜ð—Ÿð—œð—§ð—¬ ð—žð—œ ð—žð—”ð—¦ð— ð—¢ ð—žð—¢ ð—”ð—ªð—¥ ð—¦ð—œð—šð—¥ð—”ð—§ð—˜ ð—žð—œ ð—£ð—”ð—–ð—žð—˜ð—§ ð—£ð—”ð—¥ ð—Ÿð—œð—žð—›ð—œ ð—›ð—¨ð—¬ð—œ 
ð—ªð—”ð—¥ð—¡ð—œð—¡ð—š ð—žð—¢ ð——ð—¢ð—¡ð—¢ . ð—žð—¢ ð—¦ð—˜ð—¥ð—œð—¢ð—¨ð—¦ ð—¡ð—”ð—›ð—œ ð—Ÿð—˜ð—§ð—”  ðŸ‘‘â¤ï¸ðŸ’£

Â´ï½¥á´—ï½¥` ð—”ð—”ð—• ð—›ð—”ð—  ð—žð—›ð—¨ð——ð—£ð—”ð—¥ ð—™ð—›ð—œð——ð—” ð—›ð—˜ 
ð—§ð—¨ð— ð—›ð—”ð—¥ð—” ð—›ð—¨ð—¦ð—¡ ð—”ð—”ð—• ð—•ð—›ð—”ð—”ð—— ð— ð—˜ ð—ð—”ð—¬ð—˜
*à¹ á´ŠÉªsá´‹á´‡ á´Šá´€ÉªÊ™ á´á´‡ É¢á´€É´á´…ÊœÉª  á´„Êœá´Ê€Éª á´œsá´‹á´‡ á´˜Êá´€á´€Ê€ á´á´‡ á´€á´€É´á´…ÊœÉª ðŸ–¤*
"""

# Escape special markdown characters
escaped_text = escape_markdown(PM_START_TEXT, version=2)

buttons = [
    [
        InlineKeyboardButton(
            text="âœ¨â£ï¸á´€á´…á´… Êá´á´œÊ€ É¢Ê€á´˜ Ê€á´€á´…Êœá´‡ Ê€á´€á´…Êœá´‡ â£ï¸âœ¨",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true",
        ),
    ],
    [
        InlineKeyboardButton(text="Êœá´‡ÊŸá´© & á´„á´á´á´á´€É´á´…s", callback_data="help_back"),
    ],
    [
        InlineKeyboardButton(text="âœ¨â£ï¸ á´€Ê™á´á´œá´› â£ï¸âœ¨", callback_data="fallen_"),
        InlineKeyboardButton(text="âœ¨â£ï¸ sá´œá´©á´©á´Ê€á´› â£ï¸âœ¨", url=f"https://t.me/{SUPPORT_CHAT}"),
    ],
    [
        InlineKeyboardButton(text="âœ¨â£ï¸ á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€ â£ï¸âœ¨", url=f"tg://user?id={OWNER_ID}"),
        InlineKeyboardButton(text="âœ¨â£ï¸ sá´á´œÊ€á´„á´‡ â£ï¸âœ¨", callback_data="source_"),
    ],
]

HELP_STRINGS = f"""
*Â» {BOT_NAME} á´‡xá´„ÊŸá´œsÉªá´ á´‡ êœ°á´‡á´€á´›á´œÊ€á´‡s*

âž² /start : êœ±á´›á´€Ê€á´›êœ± á´á´‡ | á´€á´„á´„á´Ê€á´…ÉªÉ´É¢ á´›á´ á´á´‡ Êá´á´œ'á´ á´‡ á´€ÊŸÊ€á´‡á´€á´…Ê á´…á´É´á´‡ Éªá´›.
âž² /help  : á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ á´„á´á´á´á´€É´á´…êœ± êœ±á´‡á´„á´›Éªá´É´.
  â€£ ÉªÉ´ á´˜á´ : á´¡ÉªÊŸÊŸ êœ±á´‡É´á´… Êá´á´œ Êœá´‡ÊŸá´˜ êœ°á´Ê€ á´€ÊŸÊŸ êœ±á´œá´˜á´˜á´Ê€á´›á´‡á´… á´á´á´…á´œÊŸá´‡êœ±.
  â€£ ÉªÉ´ É¢Ê€á´á´œá´˜ : á´¡ÉªÊŸÊŸ Ê€á´‡á´…ÉªÊ€á´‡á´„á´› Êá´á´œ á´›á´ á´˜á´, á´¡Éªá´›Êœ á´€ÊŸÊŸ á´›Êœá´€á´› Êœá´‡ÊŸá´˜ á´á´á´…á´œÊŸá´‡êœ±."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("FallenRobot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="â—", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rá´œÊŸá´‡s" in IMPORTED:
                IMPORTED["rá´œÊŸá´‡s"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
    escaped_text.format(escape_markdown(first_name), BOT_NAME),
    reply_markup=InlineKeyboardMarkup(buttons),
    parse_mode=ParseMode.MARKDOWN_V2,
    timeout=60,
)
    else:
        update.effective_message.reply_photo(
            START_IMG,
            caption="Éª á´€á´ á´€ÊŸÉªá´ á´‡ Ê™á´€Ê™Ê !\n<b>Éª á´…Éªá´…É´'á´› sÊŸá´‡á´˜á´› sÉªÉ´á´„á´‡â€‹:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Â» *á´€á´ á´€ÉªÊŸá´€Ê™ÊŸá´‡ á´„á´á´á´á´€É´á´…s êœ°á´Ê€* *{}* :\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="â—", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        context.bot.answer_callback_query(query.id)

    except BadRequest:
        pass


@run_async
def Fallen_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "fallen_":
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
            text=f"*Êœá´‡Ê,*ðŸ¥€\n  *á´›ÊœÉªs Éªs {BOT_NAME}*"
            "\n*á´€ á´˜á´á´¡á´‡Ê€êœ°á´œÊŸ É¢Ê€á´á´œá´˜ á´á´€É´á´€É¢á´‡á´á´‡É´á´› Ê™á´á´› Ê™á´œÉªÊŸá´› á´›á´ Êœá´‡ÊŸá´˜ Êá´á´œ á´á´€É´á´€É¢á´‡ Êá´á´œÊ€ É¢Ê€á´á´œá´˜ á´‡á´€êœ±ÉªÊŸÊ á´€É´á´… á´›á´ á´˜Ê€á´á´›á´‡á´„á´› Êá´á´œÊ€ É¢Ê€á´á´œá´˜ êœ°Ê€á´á´ êœ±á´„á´€á´á´á´‡Ê€êœ± á´€É´á´… êœ±á´˜á´€á´á´á´‡Ê€êœ±.*"
            "\n*á´¡Ê€Éªá´›á´›á´‡É´ ÉªÉ´ á´©Êá´›Êœá´É´ á´¡Éªá´›Êœ sÇ«ÊŸá´€ÊŸá´„Êœá´‡á´Ê á´€É´á´… á´á´É´É¢á´á´…Ê™ á´€s á´…á´€á´›á´€Ê™á´€sá´‡.*"
            "\n\nâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            f"\n*âž» á´œá´©á´›Éªá´á´‡ Â»* {uptime}"
            f"\n*âž» á´œsá´‡Ê€s Â»* {sql.num_users()}"
            f"\n*âž» á´„Êœá´€á´›s Â»* {sql.num_chats()}"
            "\nâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€"
            "\n\nâž²  Éª á´„á´€É´ Ê€á´‡êœ±á´›Ê€Éªá´„á´› á´œêœ±á´‡Ê€êœ±."
            "\nâž²  Éª Êœá´€á´ á´‡ á´€É´ á´€á´…á´ á´€É´á´„á´‡á´… á´€É´á´›Éª-êœ°ÊŸá´á´á´… êœ±Êêœ±á´›á´‡á´."
            "\nâž²  Éª á´„á´€É´ É¢Ê€á´‡á´‡á´› á´œêœ±á´‡Ê€êœ± á´¡Éªá´›Êœ á´„á´œêœ±á´›á´á´Éªá´¢á´€Ê™ÊŸá´‡ á´¡á´‡ÊŸá´„á´á´á´‡ á´á´‡êœ±êœ±á´€É¢á´‡êœ± á´€É´á´… á´‡á´ á´‡É´ êœ±á´‡á´› á´€ É¢Ê€á´á´œá´˜'êœ± Ê€á´œÊŸá´‡êœ±."
            "\nâž²  Éª á´„á´€É´ á´¡á´€Ê€É´ á´œêœ±á´‡Ê€êœ± á´œÉ´á´›ÉªÊŸ á´›Êœá´‡Ê Ê€á´‡á´€á´„Êœ á´á´€x á´¡á´€Ê€É´êœ±, á´¡Éªá´›Êœ á´‡á´€á´„Êœ á´˜Ê€á´‡á´…á´‡êœ°ÉªÉ´á´‡á´… á´€á´„á´›Éªá´É´êœ± êœ±á´œá´„Êœ á´€êœ± Ê™á´€É´, á´á´œá´›á´‡, á´‹Éªá´„á´‹, á´‡á´›á´„."
            "\nâž²  Éª Êœá´€á´ á´‡ á´€ É´á´á´›á´‡ á´‹á´‡á´‡á´˜ÉªÉ´É¢ êœ±Êêœ±á´›á´‡á´, Ê™ÊŸá´€á´„á´‹ÊŸÉªêœ±á´›êœ±, á´€É´á´… á´‡á´ á´‡É´ á´˜Ê€á´‡á´…á´‡á´›á´‡Ê€á´ÉªÉ´á´‡á´… Ê€á´‡á´˜ÊŸÉªá´‡êœ± á´É´ á´„á´‡Ê€á´›á´€ÉªÉ´ á´‹á´‡Êá´¡á´Ê€á´…êœ±."
            f"\n\nâž» á´„ÊŸÉªá´„á´‹ á´É´ á´›Êœá´‡ Ê™á´œá´›á´›á´É´s É¢Éªá´ á´‡É´ Ê™á´‡ÊŸá´á´¡ Ò“á´Ê€ É¢á´‡á´›á´›ÉªÉ´É¢ Ê™á´€sÉªá´„ Êœá´‡ÊŸá´© á´€É´á´… ÉªÉ´Ò“á´ á´€Ê™á´á´œá´› {BOT_NAME}.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="sá´œá´©á´©á´Ê€á´›", callback_data="fallen_support"
                        ),
                        InlineKeyboardButton(
                            text="á´„á´á´á´á´€É´á´…s", callback_data="help_back"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€", url=f"tg://user?id={OWNER_ID}"
                        ),
                        InlineKeyboardButton(
                            text="sá´á´œÊ€á´„á´‡",
                            callback_data="source_",
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="â—", callback_data="fallen_back"),
                    ],
                ]
            ),
        )
    elif query.data == "fallen_support":
        query.message.edit_text(
            text="*à¹ á´„ÊŸÉªá´„á´‹ á´É´ á´›Êœá´‡ Ê™á´œá´›á´›á´É´s É¢Éªá´ á´‡É´ Ê™á´‡ÊŸá´á´¡ á´›á´ É¢á´‡á´› Êœá´‡ÊŸá´© á´€É´á´… á´á´Ê€á´‡ ÉªÉ´Ò“á´Ê€á´á´€á´›Éªá´É´ á´€Ê™á´á´œá´› á´á´‡.*"
            f"\n\nÉªÒ“ Êá´á´œ Ò“á´á´œÉ´á´… á´€É´Ê Ê™á´œÉ¢ ÉªÉ´ {BOT_NAME} á´Ê€ ÉªÒ“ Êá´á´œ á´¡á´€É´É´á´€ É¢Éªá´ á´‡ Ò“á´‡á´‡á´…Ê™á´€á´„á´‹ á´€Ê™á´á´œá´› á´›Êœá´‡ {BOT_NAME}, á´©ÊŸá´‡á´€sá´‡ Ê€á´‡á´©á´Ê€á´› Éªá´› á´€á´› sá´œá´©á´©á´Ê€á´› á´„Êœá´€á´›.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="sá´œá´©á´©á´Ê€á´›", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                        InlineKeyboardButton(
                            text="á´œá´©á´…á´€á´›á´‡s", url=f"https://t.me/{SUPPORT_CHAT}"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="á´…á´‡á´ á´‡ÊŸá´á´©á´‡Ê€", url=f"tg://user?id={OWNER_ID}"
                        ),
                        InlineKeyboardButton(
                            text="É¢Éªá´›Êœá´œÊ™",
                            url="https://github.com/AnonymousX1025",
                        ),
                    ],
                    [
                        InlineKeyboardButton(text="â—", callback_data="fallen_"),
                    ],
                ]
            ),
        )
    elif query.data == "fallen_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
            PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            disable_web_page_preview=True,
        )


@run_async
def Source_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text=f"""
*Êœá´‡Ê,
 á´›ÊœÉªs Éªs {BOT_NAME},
á´€É´ á´á´©á´‡É´ sá´á´œÊ€á´„á´‡ á´›á´‡ÊŸá´‡É¢Ê€á´€á´ É¢Ê€á´á´œá´© á´á´€É´á´€É¢á´‡á´á´‡É´á´› Ê™á´á´›.*

á´¡Ê€Éªá´›á´›á´‡É´ ÉªÉ´ á´©Êá´›Êœá´É´ á´¡Éªá´›Êœ á´›Êœá´‡ Êœá´‡ÊŸá´© á´Ò“ : [á´›á´‡ÊŸá´‡á´›Êœá´É´](https://github.com/LonamiWebs/Telethon)
[á´©ÊÊ€á´É¢Ê€á´€á´](https://github.com/pyrogram/pyrogram)
[á´©Êá´›Êœá´É´-á´›á´‡ÊŸá´‡É¢Ê€á´€á´-Ê™á´á´›](https://github.com/python-telegram-bot/python-telegram-bot)
á´€É´á´… á´œsÉªÉ´É¢ [sÇ«ÊŸá´€ÊŸá´„Êœá´‡á´Ê](https://www.sqlalchemy.org) á´€É´á´… [á´á´É´É¢á´](https://cloud.mongodb.com) á´€s á´…á´€á´›á´€Ê™á´€sá´‡.


*Êœá´‡Ê€á´‡ Éªs á´Ê sá´á´œÊ€á´„á´‡ á´„á´á´…á´‡ :* [É¢Éªá´›Êœá´œÊ™](https://github.com/AnonymousX1025/FallenRobot)


{BOT_NAME} Éªs ÊŸÉªá´„á´‡É´sá´‡á´… á´œÉ´á´…á´‡Ê€ á´›Êœá´‡ [á´Éªá´› ÊŸÉªá´„á´‡É´sá´‡](https://github.com/AnonymousX1025/FallenRobot/blob/master/LICENSE).
Â© 2022 - 2023 [@SFW_BotCore](https://t.me/{SUPPORT_CHAT}), á´€ÊŸÊŸ Ê€ÉªÉ¢Êœá´›s Ê€á´‡sá´‡Ê€á´ á´‡á´….
""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="â—", callback_data="source_back")]]
            ),
        )
    elif query.data == "source_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
            PM_START_TEXT.format(escape_markdown(first_name), BOT_NAME),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            disable_web_page_preview=True,
        )


@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Êœá´‡ÊŸá´˜",
                                url="https://t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
   
