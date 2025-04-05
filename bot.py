import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
)
from openai import OpenAI

# 🔐 OpenAI инициализация
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🟢 Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот с GPT. Просто напиши что-нибудь — и я отвечу 🙂")

# 💬 Ответ через GPT
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        completion = client.chat.completions.create(
            model="gpt-4",  # или "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "Ты — дружелюбный помощник, говори по делу, но просто."},
                {"role": "user", "content": user_message}
            ]
        )
        reply = completion.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")
        print(f"GPT ERROR: {e}")

# 🚀 Запуск
if __name__ == "__main__":
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден. Завершаем.")
        exit()

    print("🔁 Запускаем Telegram-бота...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("✅ Бот успешно запущен. Готов принимать сообщения!")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        stop_signals=None,
        timeout=30  # ⏱ Увеличен таймаут
    )
