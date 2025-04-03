from dotenv import load_dotenv

from rag.ai_tutor import AITutor
from rag.utils import get_gemini_llm, get_retriever
from telegram_bot.bot import TelegramBot

load_dotenv()


def create_bot():
    llm = get_gemini_llm()
    retriever = get_retriever()
    ai_tutor = AITutor(llm, retriever)

    telegram_bot = TelegramBot(ai_tutor=ai_tutor, llm=llm)
    return telegram_bot


if __name__ == "__main__":
    bot = create_bot()
    bot.run()
