import logging, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import config, database, game_logic
from telegram import ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()])
log = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    database.register_user(u.id, u.username or u.full_name)

    keyboard = [
        [KeyboardButton("🟢 START")]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await update.message.reply_text(
        "سلام! به ربات مسابقه hesam خوش آمدی.\n"
        "برای شروع مسابقه دکمه START را لمس کن.",
        reply_markup=reply_markup
    )
async def start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await quiz(update, context)
async def start_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await quiz(update, context)
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/quiz سؤال جدید\\n/score امتیاز من\\n/top جدول ۱۰ نفر برتر\\n/winners برندگان\\n/reset شروع دوباره با تأیید")

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    database.register_user(u.id, u.username or u.full_name)
    user = database.get_user(u.id)

    if user["is_winner"]:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="تبریک! شما برنده شده‌اید. برای شروع دوباره /reset را بزنید."
        )
        return

    q = game_logic.choose_question(u.id)

    if not q:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="همه سؤال‌ها را پاسخ داده‌ای. برای شروع دوباره /reset را بزن."
        )
        return

    context.user_data["pending_question"] = q

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"❓ {q['question']}\n(امتیاز این سؤال: {q['points']})"
    )
async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = context.user_data.get("pending_question")
    if not q:
        return

    u = update.effective_user
    correct = game_logic.is_correct(update.message.text, q)

    fresh = database.record_answer(
        u.id, q["id"], correct, q["points"]
    )

    context.user_data.pop("pending_question", None)

    if not fresh:
        await update.message.reply_text(
            "این سؤال قبلاً برای شما ثبت شده است."
        )
        await quiz(update, context)
        return

    if correct:
        user = database.get_user(u.id)
        msg = (
            f"✅ پاسخ درست! {q['points']} امتیاز گرفتی.\n"
            f"امتیاز کل: {user['score']}"
        )

        if game_logic.check_win(
            u.id, u.username or u.full_name
        ):
            msg += "\n🏆 تبریک! شما به ۱۰ امتیاز رسیدی و برنده شدی!"
            await update.message.reply_text(msg)
            return

        await update.message.reply_text(msg)

    else:
        await update.message.reply_text(
            "❌ پاسخ نادرست بود. پاسخ درست: "
            + " یا ".join(q["answers"])
        )

    await quiz(update, context)

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.register_user(update.effective_user.id, update.effective_user.username or update.effective_user.full_name)
    user = database.get_user(update.effective_user.id)
    await update.message.reply_text(f"امتیاز شما: {user['score']} از {config.WIN_SCORE}")

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = database.leaderboard()
    lines = ["🏅 جدول امتیازات"]
    lines += [f"{i}. {r['username']} — {r['score']} امتیاز" for i,r in enumerate(rows,1)]
    await update.message.reply_text("\\n".join(lines))

async def winners(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = database.get_winners()
    if not rows:
        await update.message.reply_text("هنوز برنده‌ای ثبت نشده است.")
        return
    await update.message.reply_text("🏆 برندگان:\\n" + "\\n".join(f"• {r['username']} — {r['score']} امتیاز" for r in rows))

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("بله، شروع مجدد", callback_data=f"reset_yes_{update.effective_user.id}"),
                                InlineKeyboardButton("لغو", callback_data=f"reset_no_{update.effective_user.id}")]])
    await update.message.reply_text("مطمئنی می‌خواهی امتیاز و سؤال‌های قبلی‌ات پاک شود؟", reply_markup=kb)

async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    action, owner = parts[1], int(parts[2])
    if query.from_user.id != owner:
        await query.answer("این دکمه برای شما نیست.", show_alert=True)
        return
    if action == "yes":
        database.register_user(owner, query.from_user.username or query.from_user.full_name)
        database.reset_user(owner)
        context.user_data.pop("pending_question", None)
        await query.edit_message_text("امتیاز و سابقه سؤال‌ها پاک شد. حالا /quiz را بزن.")
    else:
        await query.edit_message_text("عملیات لغو شد.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled bot error", exc_info=context.error)

def main():
    print(f"DEBUG_TOKEN: '{config.BOT_TOKEN}'")
    database.init_db()
    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_button, pattern="^start_quiz$"))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("winners", winners))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(reset_callback, pattern=r"^reset_(yes|no)_\\d+$"))
    app.add_handler(MessageHandler(filters.Regex("^🟢 START$"), start_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))
    app.add_error_handler(error_handler)
    log.info("hesam quiz bot is starting")
    app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()
