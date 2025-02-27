import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database.models import Topic, Exercise, Student, ExerciseHint
from typing import List
from services import StudentService, ExerciseService, TopicService, HintService, ServiceResult, SubmissionService
from telegram.helpers import escape_markdown
from http import HTTPStatus
from telegram_bot.utils import format_solution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estados de la conversación de start
STATE_GET_NAME, STATE_GET_LASTNAME, AWAITING_CODE = range(3)


class TelegramBot:
    def __init__(self, ai_tutor, llm, student_service: StudentService, exercise_service: ExerciseService,   topic_service: TopicService, hint_service: HintService, submission_service: SubmissionService):
        self.ai_tutor = ai_tutor
        self.llm = llm
        self.student_service = student_service
        self.exercise_service = exercise_service
        self.topic_service = topic_service
        self.hint_service = hint_service
        self.submission_service = submission_service
        self.app = Application.builder().token(self._get_bot_token()).build()
        self._setup_command_handlers()

    def run(self):
        """Start polling for updates."""
        self.app.run_polling()

    def _get_bot_token(self) -> str:
        """Retrieve and validate the Telegram bot token."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable is missing.")
            raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")
        return token

    def _setup_command_handlers(self):
        """Configure command and message handlers."""
        start_conversation_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.handle_start)],
            states={
                STATE_GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_name_input)],
                STATE_GET_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_lastname_input)],
            },
            fallbacks=[CommandHandler('cancel', self.handle_cancel)],
        )
        submit_conversation_handler = ConversationHandler(
            entry_points=[CommandHandler("submit", self.start_submission)],
            states={
                AWAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_code)],
            },
            fallbacks=[CommandHandler("cancel", self.handle_cancel)],
        )
        self.app.add_handler(start_conversation_handler)
        self.app.add_handler(CommandHandler("help", self.handle_help))
        self.app.add_handler(CommandHandler("ask", self.handle_user_question))
        self.app.add_handler(CommandHandler("exercise", self.handle_exercise_request))
        self.app.add_handler(CommandHandler("hint", self.handle_hint_request))
        self.app.add_handler(CommandHandler("solution", self.handle_solution_request))
        self.app.add_handler(CommandHandler("topics", self.handle_topics_list))
        self.app.add_handler(CommandHandler("topic", self.handle_topic_description))
        self.app.add_handler(submit_conversation_handler)
        self.app.add_handler(MessageHandler(filters.COMMAND, self.handle_unknown_command))

    async def handle_user_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Process a user's question and provide an AI-generated answer."""
        user_question = update.message.text.strip()
        if not user_question:
            await update.message.reply_text("Por favor, envía una pregunta válida. La pregunta no puede ser vacía.")
            return

        await update.message.reply_text("Pensando... 🤔")
        try:
            ai_response = self.ai_tutor.answer_question(user_question)
            answer = ai_response.get("answer", "Lo siento, no encontré una respuesta.")
            await update.message.reply_text(answer, parse_mode="Markdown")
        except Exception as e:
            logger.error(e)

    async def handle_start(self, update: Update, context: CallbackContext):
        """Start the user registration process."""
        user_id = str(update.message.from_user.id)
        result: ServiceResult[Student] = self.student_service.get_user(user_id=user_id)

        if result.is_success:
            user: Student = result.item
            await update.message.reply_text(f"¡Hola, {user.first_name}! 👋 Bienvenido de nuevo. Escribe /help para ver qué puedes hacer.")
            return ConversationHandler.END
        elif result.error_code == HTTPStatus.NOT_FOUND:
            await update.message.reply_text("¡Hola! 👋 Parece que es la primera vez que usas este bot. Por favor, ingresa tu nombre:")
            return STATE_GET_NAME
        else:
            logger.error(f"Error getting user: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al procesar tu solicitud :(.")
            return ConversationHandler.END

    async def handle_name_input(self, update: Update, context: CallbackContext):
        """Store the user's first name and request last name."""
        context.user_data['first_name'] = update.message.text
        await update.message.reply_text(f"Gracias, {context.user_data['first_name']}. Ahora, ingresa tus apellidos:")
        return STATE_GET_LASTNAME

    async def handle_lastname_input(self, update: Update, context: CallbackContext):
        """Complete user registration with last name."""
        user_id = str(update.message.from_user.id)
        chat_id = update.message.chat_id
        last_name = update.message.text
        first_name = context.user_data['first_name']

        result: ServiceResult[Student] = self.student_service.create_user(user_id, chat_id, first_name, last_name)
        if result.is_success:
            user = result.item
            await update.message.reply_text(f"¡Gracias, {user.first_name} {user.last_name}! 🎉 Ahora estás registrado. Escribe /help para ver qué puedes hacer.")
            return ConversationHandler.END
        else:
            logger.error(f"Error creating user: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al registrarte en el sistema :(." )
            return ConversationHandler.END

    async def handle_cancel(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Proceso cancelado.")
        return ConversationHandler.END

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Provide a list of available commands."""
        await update.message.reply_text(
            "Estos son los comandos que puedes usar:\n"
            "/start - Inicia la interacción con el bot\n"
            "/help - Obtén ayuda sobre cómo usar el bot\n"
            "/topics - Lista todos los temas\n"
            "/topic [tema] - Muestra una descripción del tema\n"
            "/ask [pregunta] - Haz una pregunta al bot\n"
            "/exercise [tema] - Solicita un ejercicio de un tema específico\n"
            "/hint [número del ejercicio] - Solicita una pista para resolver el ejercicio\n"
            "/solution [número del ejercicio] - Solicita la solución del ejercicio\n"
            "/submit [número del ejercicio] [código] - Envía tu solución para ser evaluada y recibir retroalimentación."
        )

    async def handle_topics_list(self, update: Update, context: CallbackContext):
        """Provide a list of available topics."""
        result: ServiceResult[List[Topic]] = self.topic_service.get_all()

        if not result.is_success:
            logger.error(f"Error recommending exercise: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al obtener la lista de temas :(.")
            return

        topics: List[Topic] = result.item
        if not topics:
            await update.message.reply_text("No hay temas disponibles en este momento.")
        else:
            topics_list = "\n".join([f"- {topic.name}" for topic in topics])
            await update.message.reply_text(
                f"Estos son los temas disponibles:\n{topics_list}"
            )

    async def handle_topic_description(self, update: Update, context: CallbackContext):
        """Provide a description for a specific topic."""
        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica un tema para recomendar ejercicios.")
            return

        topic_name = ' '.join(args)

        result: ServiceResult[Topic] = self.topic_service.get(name=topic_name)

        if result.is_success:
            topic: Topic = result.item
            await update.message.reply_text(topic.description)
        elif result.error_code == HTTPStatus.NOT_FOUND:
            await update.message.reply_text(f"El tema '{topic_name}' no existe. Por favor, elige otro.")
        else:
            logger.error(f"Error recommending exercise: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al obtener la descripción del tema :(.")

    async def handle_exercise_request(self, update: Update, context: CallbackContext):
        """Recommend an exercise based on the given topic."""
        user_id = str(update.effective_user.id)
        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica un tema para recomendar ejercicios.")
            return

        topic_name = ' '.join(args)

        result: ServiceResult[Exercise] = self.exercise_service.recommend_exercise(user_id, topic_name)

        if result.is_success:
            exercise: Exercise = result.item
            escaped_title = escape_markdown(exercise.title, version=2)
            formatted_exercise = format_solution(exercise.description)

            await update.message.reply_text(
                f"*{exercise.id}\. {escaped_title}*\n\n{formatted_exercise}",
                parse_mode=ParseMode.MARKDOWN_V2
            )
        elif result.error_code == HTTPStatus.NOT_FOUND:
            await update.message.reply_text("No hay ejercicios disponibles para tu nivel. ¡Buen trabajo!")
        elif result.error_code == HTTPStatus.BAD_REQUEST:
            await update.message.reply_text(result.error_message)
        else:
            logger.error(f"Error recommending exercise: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba recomendarte un ejercicio :(.")

    async def handle_hint_request(self, update: Update, context: CallbackContext):
        """Provide a hint for a given exercise."""
        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica el número del ejercicio para sugerir una pista.")
            return

        exercise_id = args[0]
        user_id = str(update.effective_user.id)

        result: ServiceResult[ExerciseHint] = self.hint_service.give_hint(user_id, exercise_id)

        if result.is_success:
            hint: ExerciseHint = result.item
            await update.message.reply_text(hint.hint_text)
        elif result.error_code == HTTPStatus.NOT_FOUND or result.error_code == HTTPStatus.BAD_REQUEST:
            await update.message.reply_text(result.error_message)
        else:
            logger.error(f"Error recommending hint: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba sugerirte una pista :(.")

    async def handle_solution_request(self, update: Update, context: CallbackContext):
        """Provide the solution for a given exercise."""
        args = context.args

        if not args:
            await update.message.reply_text("Por favor, indica el número del ejercicio para darte la solución.")
            return

        exercise_id = args[0]
        user_id = str(update.effective_user.id)

        result: ServiceResult[str] = self.exercise_service.get_solution(user_id, exercise_id)

        if result.is_success:
            formatted_solution = format_solution(result.item)
            await update.message.reply_text(formatted_solution, parse_mode=ParseMode.MARKDOWN_V2)
        elif result.error_code == HTTPStatus.NOT_FOUND or result.error_code == HTTPStatus.BAD_REQUEST:
            await update.message.reply_text(result.error_message)
        else:
            logger.error(f"Error al obtener la solución: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba darte la solución :(.")

    async def handle_solution_submission(self, update: Update, context: CallbackContext):
        """Submit an attempt for an exercise."""
        args: List[str] = context.args

        if len(args) < 2:
            await update.message.reply_text("Por favor, proporciona el número del ejercicio y el código.")
            return

        exercise_id = int(args[0])
        code = ' '.join(args[1:])
        user_id = str(update.message.from_user.id)

        result = self.submission_service.submit_code(user_id, exercise_id, code)

        if result.is_success:
            await update.message.reply_text(f"¡Intento guardado para el ejercicio '{exercise_id}'!")
        elif result.error_code == HTTPStatus.NOT_FOUND or result.error_code == HTTPStatus.BAD_REQUEST:
            await update.message.reply_text(result.error_message)
        else:
            logger.error(f"Error al obtener la solución: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al guardar el intento :(.")

    async def start_submission(self, update: Update, context: CallbackContext):
        """Recibe el número del ejercicio desde el comando y solicita el código."""
        args = context.args

        if not args or not args[0].isdigit():
            await update.message.reply_text("Por favor, proporciona el número del ejercicio. Ejemplo: /submit 1")
            return ConversationHandler.END

        exercise_id = args[0]
        context.user_data["exercise_id"] = int(exercise_id)
        await update.message.reply_text(f"Ahora introduce el código para el ejercicio '{exercise_id}'.")
        return AWAITING_CODE

    async def receive_code(self, update: Update, context: CallbackContext):
        """Recibe el código y lo envía al servicio."""
        exercise_id = context.user_data.get("exercise_id")
        user_id = str(update.message.from_user.id)
        code = update.message.text

        result = self.submission_service.submit_code(user_id, exercise_id, code)

        if result.is_success:
            await update.message.reply_text(f"¡Intento guardado para el ejercicio '{exercise_id}'!")
        elif result.error_code in {HTTPStatus.NOT_FOUND, HTTPStatus.BAD_REQUEST}:
            await update.message.reply_text(result.error_message)
        else:
            logger.error(f"Error al guardar la solución: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al guardar el intento :(.")

        return ConversationHandler.END

    async def handle_unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands by informing the user."""
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, no entiendo ese comando. 😕. Escribe /help para ver qué puedes hacer.")
