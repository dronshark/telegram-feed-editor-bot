import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from openai import OpenAI

# Состояния
WAITING_DESCRIPTION = range(1)

# Инициализация OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Сгенерировать объявления", callback_data='generate')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """Привет! Я помогу тебе создать рекламные объявления для товаров или услуг.

Напиши:
— Название товара или услуги
— Акции, бонусы или выгоды для покупателя

👇 Нажми кнопку, чтобы начать:""",
        reply_markup=reply_markup
    )

# Обработка кнопки генерации
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Напиши описание: что ты продаёшь и какие есть акции или преимущества.\n\nПример: 🚤 Продажа лодок в Москве — скидка 20%"
    )
    return WAITING_DESCRIPTION

# Генерация объявлений через GPT-4
def generate_ads(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты создаёшь продающие объявления. Каждое состоит из:\n- Заголовок 1: до 56 символов\n- Заголовок 2: до 30 символов\n- Текст: до 81 символа.\nОтвет всегда в виде трёх разных вариантов."},
                {"role": "user", "content": f"Создай объявления для: {prompt}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка при генерации: {e}"

# Получение описания и генерация
async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🔧 Генерирую объявления, подожди пару секунд...")
    ads = generate_ads(prompt)
    keyboard = [[
        InlineKeyboardButton("🔁 Перегенерировать", callback_data='regenerate'),
        InlineKeyboardButton("✏️ Изменить описание", callback_data='edit')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Вот 3 варианта 👇\n\n{ads}", reply_markup=reply_markup)
    return WAITING_DESCRIPTION

# Обработка редактирования описания
async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✏️ Хорошо, введи новое описание товара и акции.")
    return WAITING_DESCRIPTION

# Сброс и повторный старт
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот сброшен. Напиши /start, чтобы начать заново 🔁")
    return ConversationHandler.END

# Запуск с Webhook для Render Web Service
async def main():
    token = os.getenv("BOT_TOKEN")
    webhook_url = os.getenv("WEBHOOK_URL")  # Получаем WEBHOOK_URL из переменной окружения
    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_button, pattern='^generate$'))
    app.add_handler(CallbackQueryHandler(handle_button, pattern='^regenerate$'))
    app.add_handler(CallbackQueryHandler(handle_edit, pattern='^edit$'))

    # Устанавливаем Webhook URL для Telegram API
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.bot.set_webhook(url=webhook_url)

    print("🚀 Бот запущен с Webhook")
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        webhook_url=webhook_url
    )

if __name__ == "__main__":
    asyncio.run(main())
