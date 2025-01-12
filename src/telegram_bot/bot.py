import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes
from sqlalchemy.orm import Session
from database.database import SessionLocal
from database.models import User, Exercise, Topic
from database.crud import create_record, record_exists, first_or_default
from database.queries import get_highest_completed_level, get_unattempted_exercises
from dotenv import load_dotenv
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class TelegramBot:
    def __init__(self, ai_tutor, llm):
        self.ai_tutor = ai_tutor
        self.llm = llm
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Set up command and message handlers."""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ask", self.handle_message))
        self.app.add_handler(CommandHandler("exercise", self.exercise))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo))
        self.app.add_handler(MessageHandler(filters.COMMAND, self.unknown))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_question = update.message.text
        await update.message.reply_text("Thinking... 🤔")

        try:
            ai_response = self.ai_tutor.answer_question(user_question)
            answer = ai_response.get("answer", "Sorry, I couldn't find an answer.")
            await update.message.reply_text(answer, parse_mode="Markdown")
        except Exception as e:
            logger.error(e)

    async def start(self, update: Update, context: CallbackContext):
        query = update.message

        user_id = str(query.from_user.id)
        chat_id = query.chat_id
        first_name = query.from_user.first_name
        last_name = query.from_user.last_name

        try:
            with SessionLocal() as session:
                if not record_exists(session, User, user_id=user_id):
                    create_record(session, User, user_id=user_id, chat_id=chat_id, first_name=first_name, last_name=last_name)
        except Exception as e:
            logger.error(f"Error adding user: {e}")

        await update.message.reply_text(
            f"Hello, {first_name}! 👋 Welcome to the bot. "
            "Type /help to see what I can do!"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Provide help information to the user."""
        await update.message.reply_text(
            "Here are the commands you can use:\n"
            "/start - Start interacting with the bot\n"
            "/help - Get help on how to use the bot"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text='''
                                       Sorry, I didn't understand that command.''')

    # Definimos el comando /exercise
    async def exercise(self, update: Update, context: CallbackContext):
        # Extraer información del usuario
        user_id = update.effective_user.id
        session: Session = SessionLocal()
        # Obtén el resto del mensaje después del comando
        args = context.args  # Una lista de palabras separadas por espacios
        topic_name = args[0]

        try:
            with SessionLocal() as session:
                topic = first_or_default(session=session, model=Topic, name=topic_name)
                # handle null topic
                level = get_highest_completed_level(session, user_id, topic.id)
                unattempted_exercises = get_unattempted_exercises(
                    session=session, user_id=user_id, topic_id=topic.id, difficulty=level
                    )
                # Check if there are any exercises
                if unattempted_exercises:
                    # Select a random exercise
                    exercise = random.choice(unattempted_exercises)
                    await update.message.reply_text(
                        f"Te recomiendo este ejercicio:\n\n*{exercise.title}*\n\n{exercise.description}",
                        parse_mode="Markdown",
                    )
                else:
                    await update.message.reply_text("Ya no hay ejercicios disponibles para tu nivel. ¡Bien hecho!")
        except Exception as e:
            logger.error(f"Error sugesting exercise: {e}")

    def run(self):
        """Start polling for updates."""
        self.app.run_polling()
