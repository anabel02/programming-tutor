from rag.utils import get_gemini_llm, get_retriever
from rag.ai_tutor import AITutor
from telegram_bot.bot import TelegramBot
from dotenv import load_dotenv
from services import StudentService, ExerciseService, TopicService, HintService, SubmissionService

load_dotenv()


def create_bot():
    student_service = StudentService()
    topic_service = TopicService()
    exercise_service = ExerciseService()
    hint_service = HintService()
    submission_service = SubmissionService()
    llm = get_gemini_llm()
    retriever = get_retriever()
    ai_tutor = AITutor(llm, retriever)

    telegram_bot = TelegramBot(
        ai_tutor=ai_tutor,
        llm=llm,
        student_service=student_service,
        exercise_service=exercise_service,
        topic_service=topic_service,
        hint_service=hint_service,
        submission_service=submission_service
    )
    return telegram_bot


if __name__ == "__main__":
    bot = create_bot()
    bot.run()
