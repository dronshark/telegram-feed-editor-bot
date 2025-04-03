import os
from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8162979051:AAEFhuF_D7pyfNsfnbhotC9P19JhoPwGGss"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для редактирования товарных фидов.\nОтправь мне файл .csv или .xlsx, и я его обработаю!")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document
    if not os.path.exists("temp"):
        os.makedirs("temp")
    file_path = f"temp/{document.file_name}"
    file = await context.bot.get_file(document)
    await file.download_to_drive(file_path)
    await update.message.reply_text(f"Файл '{document.file_name}' получен и сохранён!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("Бот запущен...")
    app.run_polling()
