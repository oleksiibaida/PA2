import logging
from telegram import Update, ReplyKeyboardRemove, ReplyKeyboardMarkup
from telegram.ext import filters, ConversationHandler, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackContext
telegram_token = '7042430108:AAHHgHvIwWmmGVI79GVSghW4aGLP0NK8gzQ'

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hello, {update.effective_user.username}!")

async def send_message(message, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(message);

def main():
    application = ApplicationBuilder().token(telegram_token).build()
    application.add_handler(CommandHandler('start', start_command))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    # return

if __name__ == '__main__':
    main()