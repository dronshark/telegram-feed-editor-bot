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

    # Вот это сохраняет путь к файлу
    context.user_data["last_file_path"] = file_path

    await update.message.reply_text(f"Файл '{document.file_name}' получен и сохранён!")
import openai
import pandas as pd

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    file_path = context.user_data.get("last_file_path")

    if not file_path or not os.path.exists(file_path):
        await update.message.reply_text("Сначала отправь мне CSV-файл!")
        return

    df = pd.read_csv(file_path)

    # Берем только названия товаров
    names = df["name"].astype(str).tolist()

    # Формируем промпт
    prompt = f"""Ты — помощник по e-commerce. Пользователь дал такую команду: "{text}". Вот список названий товаров:
{chr(10).join(names[:20])}  # Ограничим до 20 на запрос

Измени названия товаров в соответствии с запросом. Верни только список новых названий, по одному в строку."""

    # Отправляем запрос в OpenAI
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    result_text = response.choices[0].message.content.strip()
    new_names = result_text.splitlines()

    if len(new_names) != len(df[:len(new_names)]):
        await update.message.reply_text("Что-то пошло не так. GPT вернул меньше строк, чем надо.")
        return

    df.loc[:len(new_names)-1, "name"] = new_names

    # Сохраняем новый файл
    new_path = file_path.replace(".csv", "_updated.csv")
    df.to_csv(new_path, index=False)

    await update.message.reply_document(document=open(new_path, "rb"))


if __name__ == "app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("Бот запущен...")
    app.run_polling()
