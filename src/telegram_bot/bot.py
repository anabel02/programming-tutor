import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database.database import SessionLocal
from database.models import Topic, Exercise, Student, Attempt, ExerciseHint
from typing import List
from services import StudentService, ExerciseService, TopicService, HintService, ServiceResult
from telegram.helpers import escape_markdown
from http import HTTPStatus
from telegram_bot.utils import format_solution

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Estados de la conversación de start
GET_NAME, GET_LASTNAME = range(2)


class TelegramBot:
    def __init__(self, ai_tutor, llm, student_service: StudentService, exercise_service: ExerciseService,    topic_service: TopicService, hint_service: HintService):
        self.ai_tutor = ai_tutor
        self.llm = llm
        self.student_service = student_service
        self.exercise_service = exercise_service
        self.topic_service = topic_service
        self.hint_service = hint_service
        self.app = Application.builder().token(self.get_token()).build()
        self.setup_handlers()

    def run(self):
        """Start polling for updates."""
        self.app.run_polling()

    def get_token(self) -> str:
        """Validate and return the Telegram bot token."""
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN environment variable is missing.")
            raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set.")
        return token

    def setup_handlers(self):
        """Set up command and message handlers."""
        start_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_name)],
                GET_LASTNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_lastname)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel)],
        )
        self.app.add_handler(start_handler)
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ask", self.handle_message))
        self.app.add_handler(CommandHandler("exercise", self.exercise))
        self.app.add_handler(CommandHandler("hint", self.hint_command))
        self.app.add_handler(CommandHandler("solution", self.solution_command))
        self.app.add_handler(CommandHandler("topics", self.list_topics))
        self.app.add_handler(CommandHandler("topic", self.topic_description))
        self.app.add_handler(CommandHandler("submit", self.submission))
        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.echo))
        self.app.add_handler(MessageHandler(filters.COMMAND, self.unknown))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_question = update.message.text

        if not user_question or user_question.strip() == "":
            await update.message.reply_text("Por favor, envía una pregunta válida. La pregunta no puede ser vacía.")
            return

        await update.message.reply_text("Pensando... 🤔")

        try:
            ai_response = self.ai_tutor.answer_question(user_question)
            answer = ai_response.get("answer", "Lo siento, no encontré una respuesta.")
            await update.message.reply_text(answer, parse_mode="Markdown")
        except Exception as e:
            logger.error(e)

    async def start(self, update: Update, context: CallbackContext):
        user_id = str(update.message.from_user.id)

        result: ServiceResult[Student] = self.student_service.get_user(user_id=user_id)
        if result.is_success:
            user: Student = result.item
            await update.message.reply_text(
                f"¡Hola, {user.first_name}! 👋 Bienvenido de nuevo al bot. "
                "Escribe /help para ver lo que puedo hacer."
            )
            return ConversationHandler.END
        elif result.error_code == HTTPStatus.NOT_FOUND:
            await update.message.reply_text(
                "¡Hola! 👋 Parece que es la primera vez que usas este bot. "
                "Por favor, ingresa tu nombre:"
            )
            return GET_NAME  # Pasa al estado GET_NAME
        else:
            await update.message.reply_text("Ocurrió un error al procesar tu solicitud :(.")
            return ConversationHandler.END

    async def get_name(self, update: Update, context: CallbackContext):
        first_name = update.message.text

        # Guarda el nombre en el contexto de la conversación
        context.user_data['first_name'] = first_name

        await update.message.reply_text(
            f"Gracias, {first_name}. Ahora, por favor, ingresa tus apellidos:"
        )
        return GET_LASTNAME  # Pasa al estado GET_LASTNAME

    async def get_lastname(self, update: Update, context: CallbackContext):
        user_id = str(update.message.from_user.id)
        chat_id = update.message.chat_id
        last_name = update.message.text
        first_name = context.user_data['first_name']  # Recupera el nombre del contexto

        result: ServiceResult[Student] = self.student_service.create_user(user_id, chat_id, first_name, last_name)
        if result.is_success:
            user = result.item
            await update.message.reply_text(
                    f"¡Gracias, {user.first_name} {user.last_name}! 🎉 Ahora estás registrado en el sistema. "
                    "Escribe /help para ver lo que puedo hacer."
                )
            return ConversationHandler.END  # Termina la conversación
        else:
            logger.error(f"Error recommending exercise: {result.error_message}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al registrarte en el sistema :(.")
            return ConversationHandler.END  # Termina la conversación en caso de error

    async def cancel(self, update: Update, context: CallbackContext):
        await update.message.reply_text("Registro cancelado.")
        return ConversationHandler.END

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Estos son los comandos que puedes usar:\n"
            "/start - Inicia la interacción con el bot\n"
            "/help - Obtén ayuda sobre cómo usar el bot\n"
            "/topics - Lista todos los temas\n"
            "/topic [tema] - Muestra una descripción del tema\n"
            "/ask [pregunta] - Haz una pregunta al bot\n"
            "/exercise [tema] - Solicita un ejercicio de un tema específico\n"
            "/hint [número del ejercicio] - Solicita una pista para resolver el ejercicio\n"
            "/solution [número del ejercicio] - Solicita la solución del ejercicio"
        )

    async def list_topics(self, update: Update, context: CallbackContext):
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

    async def topic_description(self, update: Update, context: CallbackContext):
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

    async def exercise(self, update: Update, context: CallbackContext):
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
            formatted_exercise = self.format_solution(exercise.description)

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

    async def hint_command(self, update: Update, context: CallbackContext):
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

    async def solution_command(self, update: Update, context: CallbackContext):
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

    async def submission(self, update: Update, context: CallbackContext):
        args: List[str] = context.args

        if len(args) < 2:
            await update.message.reply_text("Por favor, proporciona el número del ejercicio y el código.")
            return

        exercise_id = int(args[0])
        code = ' '.join(args[1:])
        user_id = str(update.message.from_user.id)

        try:
            with SessionLocal() as session:
                exercise: Exercise = self.exercise_service.get_by(session, id=exercise_id)
                if not exercise:
                    await update.message.reply_text(f"El ejercicio con número {exercise_id} no existe.")
                    return

                student: Student = self.student_service.first_or_default(session=session, user_id=user_id)
                if not student:
                    await update.message.reply_text("El estudiante no está registrado.")
                    return

                if exercise.id not in {ex.id for ex in student.exercises}:
                    await update.message.reply_text("Parece que no te he recomendado ese ejercicio.")
                    return

                new_attempt = Attempt(
                    student_id=student.id,
                    exercise_id=exercise_id,
                    submitted_code=code,
                )

                session.add(new_attempt)
                session.commit()

                await update.message.reply_text(f"¡Intento guardado para el ejercicio '{exercise.title}'!")

        except ValueError:
            await update.message.reply_text("El ID del ejercicio debe ser un número entero.")
        except Exception as e:
            logger.error(f"Error al guardar el intento: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al guardar el intento :(.")

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

    async def unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Lo siento, no entiendo ese comando. 😕")
