import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# Инициализация OpenAI клиента
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с GPT. Напиши что-нибудь — и я отвечу 🧠")

# Ответ через GPT
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    try:
        completion = client.chat.completions.create(
            model="gpt-4",  # можно поменять на "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "Ты — дружелюбный помощник, который отвечает ясно и полезно."},
                {"role": "user", "content": user_message}
            ]
        )

        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Запуск
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ Не найден BOT_TOKEN в переменных окружения")
        exit()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✅ Бот запущен")
    app.run_polling()
