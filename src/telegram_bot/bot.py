import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes
from database.database import SessionLocal
from database.models import User, Topic, Exercise
from typing import List
from telegram_bot.user_service import UserService
from telegram_bot.exercise_service import ExerciseService
from telegram_bot.topic_service import TopicService
from telegram_bot.hints_service import HintService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    def __init__(self, ai_tutor, llm):
        self.ai_tutor = ai_tutor
        self.llm = llm
        self.app = Application.builder().token(self.get_token()).build()
        self.setup_handlers()

    def get_token(self) -> str:
        """Validate and return the Telegram bot token."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable is missing.")
            raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")
        return token

    def setup_handlers(self):
        """Set up command and message handlers."""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ask", self.handle_message))
        self.app.add_handler(CommandHandler("exercise", self.exercise))
        self.app.add_handler(CommandHandler("hint", self.hint_command))
        self.app.add_handler(CommandHandler("topics", self.list_topics))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo))
        self.app.add_handler(MessageHandler(filters.COMMAND, self.unknown))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_question = update.message.text
        await update.message.reply_text("Pensando... 🤔")

        try:
            ai_response = self.ai_tutor.answer_question(user_question)
            answer = ai_response.get("answer", "Lo siento, no encontré una respuesta.")
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
                user: User = UserService.get_or_create_user(session, user_id, chat_id, first_name, last_name)
                await update.message.reply_text(
                    f"¡Hola, {user.first_name}! 👋 Bienvenido al bot. "
                    "Escribe /help para ver lo que puedo hacer."
                )
        except Exception as e:
            logger.error(f"Error adding user: {e}")
            await update.message.reply_text("An error occurred while adding you to the system.")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Provide help information to the user."""
        await update.message.reply_text(
            "Estos son los comandos que puedes usar:\n"
            "/start - Inicia la interacción con el bot\n"
            "/help - Obtén ayuda sobre cómo usar el bot\n"
            "/topics - Lista todos los temas\n"
            "/ask [pregunta] - Haz una pregunta al bot\n"
            "/exercise [tema] - Solicita un ejercicio de un tema específico\n"
            "/hint [número del ejercicio] - Solicita una pista para resolver el ejercicio"
        )

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, no entiendo ese comando. 😕")

    async def exercise(self, update: Update, context: CallbackContext):
        user_id = str(update.effective_user.id)
        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica un tema para recomendar ejercicios.")
            return

        topic_name = args[0]

        try:
            with SessionLocal() as session:
                user: User = UserService.first_or_default(session=session, user_id=user_id)
                if not user:
                    await update.message.reply_text("No se encontró al usuario en el sistema.")
                    return

                topic: Topic = TopicService.get_by(session=session, name=topic_name)
                if not topic:
                    await update.message.reply_text(f"El tema '{topic_name}' no existe. Por favor, elige otro.")
                    return

                exercise: Exercise = ExerciseService.recommend_exercise(session, user, topic)
                if exercise:
                    await update.message.reply_text(
                        f"Aquí tienes un ejercicio para practicar:\n\n*{exercise.id}.{exercise.title}*\n\n{exercise.description}",
                        parse_mode="MarkdownV2"
                    )
                else:
                    await update.message.reply_text("No hay ejercicios disponibles para tu nivel. ¡Buen trabajo!")
        except Exception as e:
            logger.error(f"Error recommending exercise: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba recomendarte un ejercicio :(.")

    def parse_hint_command(self, command: str):
        # Ensure the command starts with /hint
        if not command.startswith("/hint"):
            return None, None

        # Extract arguments (remove the command prefix)
        parts = command[6:].strip().split(" ", 1)  # Split into topic and exercise
        if len(parts) < 2:
            return None, None

        topic, exercise = parts
        return topic.strip(), exercise.strip()

    async def hint_command(self, update: Update, context: CallbackContext):
        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica el número del ejercicio para sugerir una pista.")
            return

        exercise_id = args[0]

        user_id = str(update.effective_user.id)

        try:
            with SessionLocal() as session:
                # Llamar a la función para obtener la pista
                hint = HintService.give_hint(session, user_id, exercise_id)

                # Responder al usuario
                await update.message.reply_text(hint)
        except Exception as e:
            logger.error(f"Error recommending exercise: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba sugerirte una pista :(.")

    async def list_topics(self, update: Update, context: CallbackContext):
        """List all available topics."""
        try:
            with SessionLocal() as session:
                topics = TopicService.get_all(session)
                if not topics:
                    await update.message.reply_text("No hay temas disponibles en este momento.")
                    return

                topics_list = "\n".join([f"- {topic.name}" for topic in topics])
                await update.message.reply_text(
                    f"Estos son los temas disponibles:\n{topics_list}"
                )
        except Exception as e:
            logger.error(f"Error fetching topics: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al obtener la lista de temas.")

    def run(self):
        """Start polling for updates."""
        self.app.run_polling()
