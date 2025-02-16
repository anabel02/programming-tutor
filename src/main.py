from rag.utils import get_gemini_llm, get_retriever
from rag.ai_tutor import AITutor
from telegram_bot.bot import TelegramBot
from dotenv import load_dotenv
from services import StudentService, ExerciseService, TopicService, HintService

load_dotenv()


def create_bot():
    student_service = StudentService()
    exercise_service = ExerciseService()
    topic_service = TopicService()
    hint_service = HintService()
    llm = get_gemini_llm()
    retriever = get_retriever()
    ai_tutor = AITutor(llm, retriever)

    bot = TelegramBot(
        ai_tutor=ai_tutor,
        llm=llm,
        student_service=student_service,
        exercise_service=exercise_service,
        topic_service=topic_service,
        hint_service=hint_service
    )
    return bot


if __name__ == "__main__":
    bot = create_bot()
    bot.run()
