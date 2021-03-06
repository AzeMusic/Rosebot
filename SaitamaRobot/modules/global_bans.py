import html
import time
from datetime import datetime
from io import BytesIO
from SaitamaRobot.modules.sql.users_sql import get_user_com_chats
import SaitamaRobot.modules.sql.global_bans_sql as sql
from SaitamaRobot import (DEV_USERS, EVENT_LOGS, OWNER_ID, STRICT_GBAN, DRAGONS,
                          SUPPORT_CHAT, SPAMWATCH_SUPPORT_CHAT, DEMONS, TIGERS,
                          WOLVES, sw, dispatcher)
from SaitamaRobot.modules.helper_funcs.chat_status import (is_user_admin,
                                                           support_plus,
                                                           user_admin)
from SaitamaRobot.modules.helper_funcs.extraction import (extract_user,
                                                          extract_user_and_text)
from SaitamaRobot.modules.helper_funcs.misc import send_to_list
from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, run_async)
from telegram.utils.helpers import mention_html

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@run_async
@support_plus
def gban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(
            "Bir istifad????iy?? istinad etmirsiniz.."
        )
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "Bu istifad????i ElnurSoBot-in bir par??as??d??r\nOna qar???? bunu ed?? bilm??r??m."
        )
        return

    if int(user_id) in DRAGONS:
        message.reply_text(
            "M??n balaca g??zl??rim il?? a??lay??ram... sudo istifad????i m??harib??si! Siz niy?? bir biriniz?? bunu edirsiniz?"
        )
        return

    if int(user_id) in DEMONS:
        message.reply_text(
            "OOOH kims?? ??eytan istifad????imizi gban etm??y?? ??al??????r! *??lin?? popkorn alaraq*")
        return

    if int(user_id) in TIGERS:
        message.reply_text("O p??l??ngdir! Banlana bilm??z!")
        return

    if int(user_id) in WOLVES:
        message.reply_text("yox, o bir Canavard??r! Banlana bilmirl??r!")
        return

    if user_id == bot.id:
        message.reply_text("h?? h?? g??zl?? ??z??m?? gban edim?")
        return

    if user_id in [777000, 1087968824]:
        message.reply_text("Axmaq! Telegrama h??cum ????km??y?? ??al??????r!")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("??stifad????i tap??lmad??.")
            return ""
        else:
            return

    if user_chat.type != 'private':
        message.reply_text("Bu bir istifad????i deyil!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            message.reply_text(
                "Bu istifad????i onsuz da gban edilib; S??b??bi d??yi????rdim amma bir s??b??b verm??mis??n..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text(
                "Bu istifad????i onsuz da gban edilib, k??hn?? s??b??b:\n"
                "<code>{}</code>\n"
                "M??n k??hn?? s??b??bi yenisi il?? ??v??z etdim!".format(
                    html.escape(old_reason)),
                parse_mode=ParseMode.HTML)

        else:
            message.reply_text(
                "Bu istifad????i onsuz da gban edilib, amma bir s??b??b verilm??mi??di; Art??q bir s??b??b var!"
            )

        return

    message.reply_text("za!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = "<b>{} ({})</b>\n".format(
            html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f"\n<b>S??b??b:</b> <a href=\"https://telegram.me/{chat.username}/{message.message_id}\">{reason}</a>"
        else:
            log_message += f"\n<b>S??b??b:</b> <code>{reason}</code>"

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS, log_message +
                "\n\nX??ta ba?? verdi.")

    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Gban etm??k m??mk??n olmad??. X??ta: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Gban etm??k m??mk??n olmad??. X??ta: {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    send_to_list(bot, DRAGONS + DEMONS,
                                 f"Gban etm??k olmad??. X??ta: {excp.message}")
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if EVENT_LOGS:
        log.edit_text(
            log_message +
            f"\n<b>Banland?????? qruplar:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(
            bot,
            DRAGONS + DEMONS,
            f"Gban tamamland??! (??stifad????i <code>{gbanned_chats}</code> qrupdan banland??)",
            html=True)

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
        message.reply_text("Haz??r! Gban edildi.", parse_mode=ParseMode.HTML)
    else:
        message.reply_text("Haz??r! Gban edildi.", parse_mode=ParseMode.HTML)

    try:
        bot.send_message(
            user_id, "#EVENT"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
            f"</b>Appeal Chat:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML)
    except:
        pass  # bot probably blocked by user


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "Bir istifad????iy?? istinad etmirsiniz.."
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("Bu bir istifad????i deyil!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("Bu istifad????i gban edilm??yib!")
        return

    message.reply_text(
        f"M??n {user_chat.first_name} istifad????isin?? qlobal olaraq 2-ci ??ans verir??m.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != 'private':
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS, log_message +
                "\n\nX??ta ba?? verdi.")
    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Gban?? silm??k u??ursuz oldu. X??ta: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Gban?? silm??k u??ursuz oldu. X??ta: {excp.message}",
                        parse_mode=ParseMode.HTML)
                else:
                    bot.send_message(
                        OWNER_ID, f"Gban?? silm??k u??ursuz oldu. X??ta: {excp.message}")
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Gban??n silindiyi qruplar:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, DRAGONS + DEMONS, "Gban?? silm??k tamamland??!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(
            f"Gban silindi. Silinm?? prosesi {ungban_time} ????kdi")
    else:
        message.reply_text(
            f"Person has been un-gbanned. Took {ungban_time} sec")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "Gban alm???? istifad????i yoxdur...")
        return

    banfile = 'A??a????dak??lar il?? vidala????n.\n'
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"S??b??b: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Gban alm???? istifad????il??rin siyah??s??.")


def check_and_ban(update, user_id, should_message=True):

    chat = update.effective_chat  # type: Optional[Chat]
    try:
        sw_ban = sw.get_ban(int(user_id))
    except AttributeError:
        sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"<b>Diqq??t</b>: Bu istifad????i qlobal olaraq banland??.\n"
                f"<code>*onu buradan banlay??ram*</code>.\n"
                f"<b>Appeal chat</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>ID</b>: <code>{sw_ban.id}</code>\n"
                f"<b>S??b??b</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML)
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = f"<b>Diqq??t</b>: Bu istifad????i qlobal olaraq banland??.\n" \
                   f"<code>*onu buradan banlay??ram*</code>.\n" \
                   f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n" \
                   f"<b>ID</b>: <code>{user_id}</code>"
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>S??b??b:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    if sql.does_chat_gban(
            update.effective_chat.id) and update.effective_chat.get_member(
                bot.id).can_restrict_members:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "Antispam aktivdir ???")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("Antispam deaktivdir ???")
    else:
        update.effective_message.reply_text(
            "M??n?? bir arqument verm??lis??n! on/off, yes/no!\n\n"
            "Haz??rki ayar: {}\n"
            "Aktiv olduqda gban bu bu qrupa t??sir ed??c??k. ??ks halda yox.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return f"??? {sql.num_gbanned_users()} gban edilmi?? istifad????i."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Z??r??rlidirmi: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in DRAGONS + TIGERS + WOLVES:
        return ""
    if is_gbanned:
        text = text.format("H??")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\n<b>S??b??b:</b> <code>{html.escape(user.reason)}</code>"
        text += f"\n<b>M??raci??t:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("???")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"Gban bu qrupa t??sir edirmi: `{sql.does_chat_gban(chat_id)}`."


__help__ = f"""
*Sad??c?? adminl??r:*
 ??? `/antispam <on/off/yes/no>`*:* antispam aktiv/deaktiv ed??r.

B??t??n qruplar aras??nda spam g??nd??rm??l??ri qada??an etm??k ??????n bot devl??ri t??r??find??n \
istifad?? edil??n Anti-Spam. Bu, spam da??q??nlar??n?? m??mk??n q??d??r tez silm??kl?? sizi v?? qruplar??n??z?? qoruma??a k??m??k edir.
*Qeyd:* @{SUPPORT_CHAT} qrupunda bel?? istifad????il??ri ??ikay??t ed?? bil??rsiniz

Bu, spam g??nd??ricil??ri s??hb??t ota????n??zdan m??mk??n q??d??r ??ox ????xarmaq ??????n @Spamwatch API-ni d?? birl????dirir!
*SpamWatch n??dir?*
SpamWatch spam botlar, trollar, bitkoin spamerl??ri v?? xo??ag??lm??z simvollar??n daima yenil??n??n b??y??k bir siyah??s??n?? saxlay??r.[.](https://telegra.ph/file/f584b643c6f4be0b1de53.jpg)
Daim avtomatik olaraq qrupunuzdan spam g??nd??rm??yin qada??an olunmas??na k??m??k edir. Bel??likl??, spammerl??rin qrupunuza h??cum etm??sind??n narahat olmayacaqs??n??z..
*Qeyd:* ??stifad????il??r spam izl??m?? qada??alar??na @SpamwatchSupport ??nvan??ndan m??raci??t ed?? bil??rl??r
"""

GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
