import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes
from sqlalchemy.orm import Session
from telegram_bot.database import SessionLocal
from telegram_bot.models import user_exercise, User, Exercise
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

        # Obtener el nivel más avanzado completado por el usuario
        completed_difficulties = session.execute(
            user_exercise.select()
            .where(user_exercise.c.user_id == user_id)
        ).fetchall()

        if completed_difficulties:
            # Determinar el nivel más avanzado completado
            completed_levels = [row.difficulty for row in completed_difficulties]
            next_level = self.get_next_difficulty(max(completed_levels))

            # Buscar ejercicios de arrays en el siguiente nivel
            exercises = session.query(Exercise).filter(
                Exercise.difficulty == next_level,
                Exercise.topic.has('conditionals')
            ).all()

            if exercises:
                # Elegir un ejercicio aleatoriamente
                exercise = random.choice(exercises)
                update.message.reply_text(
                    f"Te recomiendo este ejercicio:\n\n*{exercise.title}*\n\n{exercise.description}",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text("No hay ejercicios disponibles para tu nivel. ¡Bien hecho!")
        else:
            await update.message.reply_text("Parece que aún no has completado ningún ejercicio. ¡Empieza con uno básico!")

    # Función auxiliar para obtener el siguiente nivel de dificultad
    def get_next_difficulty(self, current_level):
        levels = ["Basic", "Intermediate", "Advanced"]
        try:
            return levels[levels.index(current_level) + 1]
        except IndexError:
            return "Advanced"  # Ya está en el nivel máximo

    def run(self):
        """Start polling for updates."""
        self.app.run_polling()
