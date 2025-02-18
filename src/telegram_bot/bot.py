import logging
import os
from telegram import Update
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from database.database import SessionLocal
from database.models import Topic, Exercise, ExerciseHint, Student, Attempt
from typing import List
from services import StudentService, ExerciseService, TopicService, HintService
from telegram.helpers import escape_markdown

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
        """
        Maneja el comando /start. Si el usuario no está en la base de datos,
        solicita su nombre y apellidos.
        """
        query = update.message
        user_id = str(query.from_user.id)

        try:
            with SessionLocal() as session:
                user = self.student_service.first_or_default(session, user_id=user_id)
                if user:
                    await update.message.reply_text(
                        f"¡Hola, {user.first_name}! 👋 Bienvenido de nuevo al bot. "
                        "Escribe /help para ver lo que puedo hacer."
                    )
                else:
                    await update.message.reply_text(
                        "¡Hola! 👋 Parece que es la primera vez que usas este bot. "
                        "Por favor, ingresa tu nombre:"
                    )
                    return GET_NAME  # Pasa al estado GET_NAME
        except Exception as e:
            logger.error(f"Error al verificar el usuario: {e}")
            await update.message.reply_text("Ocurrió un error al procesar tu solicitud :(.")

    async def get_name(self, update: Update, context: CallbackContext):
        """
        Captura el nombre del usuario y solicita sus apellidos.
        """
        first_name = update.message.text

        # Guarda el nombre en el contexto de la conversación
        context.user_data['first_name'] = first_name

        await update.message.reply_text(
            f"Gracias, {first_name}. Ahora, por favor, ingresa tus apellidos:"
        )
        return GET_LASTNAME  # Pasa al estado GET_LASTNAME

    async def get_lastname(self, update: Update, context: CallbackContext):
        """
        Captura los apellidos del usuario y lo registra en la base de datos.
        """
        user_id = str(update.message.from_user.id)
        chat_id = update.message.chat_id
        last_name = update.message.text
        first_name = context.user_data['first_name']  # Recupera el nombre del contexto

        try:
            with SessionLocal() as session:
                # Crea el usuario en la base de datos
                user = self.student_service.create_user(session, user_id, chat_id, first_name, last_name)
                await update.message.reply_text(
                    f"¡Gracias, {user.first_name} {user.last_name}! 🎉 Ahora estás registrado en el sistema. "
                    "Escribe /help para ver lo que puedo hacer."
                )
                return ConversationHandler.END  # Termina la conversación
        except Exception as e:
            logger.error(f"Error al registrar el usuario: {e}")
            await update.message.reply_text("Ocurrió un error al registrarte en el sistema :(.")
            return ConversationHandler.END  # Termina la conversación en caso de error

    async def cancel(self, update: Update, context: CallbackContext):
        """
        Cancela la conversación.
        """
        await update.message.reply_text("Registro cancelado.")
        return ConversationHandler.END

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

        topic_name = ' '.join(args)

        try:
            with SessionLocal() as session:
                user: Student = self.student_service.first_or_default(session=session, user_id=user_id)
                if not user:
                    await update.message.reply_text("No se encontró al usuario en el sistema.")
                    return

                topic: Topic = self.topic_service.get_by(session=session, name=topic_name)
                if not topic:
                    await update.message.reply_text(f"El tema '{topic_name}' no existe. Por favor, elige otro.")
                    return
                exercise: Exercise = self.exercise_service.recommend_exercise(session, user, topic)
                if exercise:
                    escaped_title = escape_markdown(exercise.title, version=2)
                    escaped_description = escape_markdown(exercise.description, version=2)

                    await update.message.reply_text(
                        f"Aquí tienes un ejercicio para practicar:\n\n*{exercise.id}\. {escaped_title}*\n\n{escaped_description}",
                        parse_mode="MarkdownV2"
                    )
                else:
                    await update.message.reply_text("No hay ejercicios disponibles para tu nivel. ¡Buen trabajo!")
        except Exception as e:
            logger.error(f"Error recommending exercise: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba recomendarte un ejercicio :(.")

    async def hint_command(self, update: Update, context: CallbackContext):
        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica el número del ejercicio para sugerir una pista.")
            return

        exercise_id = args[0]

        user_id = str(update.effective_user.id)

        try:
            with SessionLocal() as session:
                hint: ExerciseHint = self.hint_service.give_hint(session, user_id, exercise_id)
                await update.message.reply_text(hint)
        except Exception as e:
            logger.error(f"Error recommending exercise: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba sugerirte una pista :(.")

    async def solution_command(self, update: Update, context: CallbackContext):
        """
        Proporciona la solución de un ejercicio, formateando correctamente el código C# y el texto.
        """
        args = context.args

        if not args:
            await update.message.reply_text("Por favor, indica el número del ejercicio para darte la solución.")
            return

        exercise_id = args[0]

        try:
            with SessionLocal() as session:
                exercise: Exercise = self.exercise_service.get_by(session, id=exercise_id)
                if not exercise.solution:
                    await update.message.reply_text("No tenemos solución para este ejercicio.")
                    return

                formatted_solution = self.format_solution(exercise.solution)
                await update.message.reply_text(formatted_solution, parse_mode=ParseMode.MARKDOWN_V2)
        except Exception as e:
            logger.error(f"Error al obtener la solución: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error mientras intentaba darte la solución :(.")

    def format_solution(self, solution: str) -> str:
        """
        Formatea la solución para que el código C# y el texto se muestren correctamente en MarkdownV2.

        Args:
            solution (str): La solución del ejercicio, que puede contener código C# y texto.

        Returns:
            str: La solución formateada en MarkdownV2.
        """
        parts = solution.split("```")
        formatted_parts = []

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Es texto, escapa los caracteres especiales de MarkdownV2
                formatted_parts.append(escape_markdown(part, version=2))
            else:
                # Es código C#, envuélvelo en un bloque de código
                formatted_parts.append(f"```csharp{part[6:]}```")

        return "".join(formatted_parts)

    async def list_topics(self, update: Update, context: CallbackContext):
        """List all available topics."""
        try:
            with SessionLocal() as session:
                topics = self.topic_service.get_all(session)
                if not topics:
                    await update.message.reply_text("No hay temas disponibles en este momento.")
                    return

                topics_list = "\n".join([f"- {topic.name}" for topic in topics])
                await update.message.reply_text(
                    f"Estos son los temas disponibles:\n{topics_list}"
                )
        except Exception as e:
            logger.error(f"Error fetching topics: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al obtener la lista de temas :(.")

    async def topic_description(self, update: Update, context: CallbackContext):
        """Show the description of a given topic"""

        args: List[str] = context.args

        if not args:
            await update.message.reply_text("Por favor, indica un tema para recomendar ejercicios.")
            return

        topic_name = ' '.join(args)

        try:
            with SessionLocal() as session:
                topic: Topic = self.topic_service.get_by(session, name=topic_name)
                if not topic:
                    await update.message.reply_text(f"El tema '{topic_name}' no existe. Por favor, elige otro.")
                    return

                await update.message.reply_text(topic.description)
        except Exception as e:
            logger.error(f"Error fetching topics: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al obtener la descripción del tema :(.")

    async def submission(self, update: Update, context: CallbackContext):
        args: List[str] = context.args

        # Verifica que se hayan proporcionado los argumentos necesarios
        if len(args) < 2:
            await update.message.reply_text("Por favor, proporciona el ID del ejercicio y el código. Ejemplo: /submit 1 'Console.WriteLine(\"Hola mundo\")'")
            return

        try:
            # Obtén el ID del ejercicio y el código de los argumentos
            exercise_id = int(args[0])  # El primer argumento es el ID del ejercicio
            code = ' '.join(args[1:])  # El resto de los argumentos son el código

            # Obtén el ID del estudiante (usuario de Telegram)
            user_id = str(update.message.from_user.id)

            # Crea una sesión de base de datos
            with SessionLocal() as session:
                # Verifica si el ejercicio existe
                exercise: Exercise = self.exercise_service.get_by(session, id=exercise_id)
                if not exercise:
                    await update.message.reply_text(f"El ejercicio con ID {exercise_id} no existe.")
                    return

                # Verifica si el estudiante existe
                student: Student = self.student_service.first_or_default(session=session, user_id=user_id)
                if not student:
                    await update.message.reply_text(f"El estudiante con user_id {user_id} no está registrado.")
                    return

                # Crea un nuevo Attempt
                new_attempt = Attempt(
                    student_id=student.id,
                    exercise_id=exercise_id,
                    submitted_code=code,
                )

                # Guarda el Attempt en la base de datos
                session.add(new_attempt)
                session.commit()

                # Confirma al usuario que el intento se ha guardado
                await update.message.reply_text(f"¡Intento guardado para el ejercicio '{exercise.title}'!")

        except ValueError:
            await update.message.reply_text("El ID del ejercicio debe ser un número entero.")
        except Exception as e:
            logger.error(f"Error al guardar el intento: {e}", exc_info=True)
            await update.message.reply_text("Ocurrió un error al guardar el intento :(.")

    def run(self):
        """Start polling for updates."""
        self.app.run_polling()
