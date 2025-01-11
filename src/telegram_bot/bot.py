import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes
from sqlalchemy.orm import Session
from telegram_bot.database import SessionLocal, User
from rag.main import ai_tutor
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_question = update.message.text
    await update.message.reply_text("Thinking... 🤔")

    try:
        ai_response = ai_tutor.answer_question(user_question)
        answer = ai_response.get("answer", "Sorry, I couldn't find an answer.")
        await update.message.reply_text(answer, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def start(update: Update, context: CallbackContext):
    query = update.message

    user_id = str(query.from_user.id)
    chat_id = query.chat_id
    first_name = query.from_user.first_name
    last_name = query.from_user.last_name

    session: Session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user is None:
            user = User(user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
            session.add(user)
        session.commit()
    except Exception as e:
        logger.error(f"Error setting language: {e}")
    finally:
        session.close()

    await update.message.reply_text(
        f"Hello, {first_name}! 👋 Welcome to the bot. "
        "Type /help to see what I can do!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide help information to the user."""
    await update.message.reply_text(
        "Here are the commands you can use:\n"
        "/start - Start interacting with the bot\n"
        "/help - Get help on how to use the bot"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", handle_message))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    app.run_polling()
