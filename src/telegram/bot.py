import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, Application, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Subscription

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = '7556696845:AAFh6s6NBiS-WNrhk67Kra3EWJzqTWy8sK8'


async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Other Language", callback_data='lang_other')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome! Please choose your language:', reply_markup=reply_markup)


# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await context.bot.send_message(
#         chat_id=update.effective_chat.id,
#         text="I'm a bot, please talk to me!"
#     )


async def set_language(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    print('='*50)
    print(query.from_user)
    print('='*50)
    user_id = str(query.from_user.id)
    chat_id = query.message.chat_id

    language = 'en' if query.data == 'lang_en' else 'other'

    session: Session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            user.language = language
        else:
            user = User(user_id=user_id, chat_id=chat_id, language=language)
            session.add(user)
        session.commit()
        await query.edit_message_text(text=f"Language set to {language}.")
    except Exception as e:
        logger.error(f"Error setting language: {e}")
    finally:
        session.close()


async def subscribe(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    chat_id = update.message.chat_id

    session: Session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id, chat_id=chat_id)
            session.add(user)
            session.commit()

        subscription = session.query(Subscription).filter(Subscription.user_id == user_id).first()
        if subscription:
            subscription.subscribed = True
        else:
            subscription = Subscription(user_id=user_id, subscribed=True)
            session.add(subscription)
        session.commit()
        await update.message.reply_text('Subscribed successfully.')
    except Exception as e:
        logger.error(f"Error during subscription: {e}")
    finally:
        session.close()


async def unsubscribe(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)

    session: Session = SessionLocal()
    try:
        subscription = session.query(Subscription).filter(Subscription.user_id == user_id).first()
        if subscription:
            subscription.subscribed = False
            session.commit()
            await update.message.reply_text('Unsubscribed successfully.')
        else:
            await update.message.reply_text('You are not subscribed.')
    except Exception as e:
        logger.error(f"Error during unsubscription: {e}")
    finally:
        session.close()


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_language, pattern='^lang_'))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    app.add_handler(CommandHandler('caps', caps))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    app.run_polling()


if __name__ == '__main__':
    main()
