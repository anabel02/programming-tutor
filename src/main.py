from rag.utils import get_gemini_llm, get_retriever
from rag.ai_tutor import AITutor
from telegram_bot.bot import TelegramBot

if __name__ == "__main__":
    llm = get_gemini_llm()
    retriever = get_retriever()
    ai_tutor = AITutor(llm, retriever)

    question = "array bidimensional"
    answer = ai_tutor.answer_question(question)
    print(answer['answer'])

    bot = TelegramBot(ai_tutor)
    bot.run()
