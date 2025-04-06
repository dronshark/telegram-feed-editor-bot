import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)
from openai import OpenAI
import asyncio

WAITING_DESCRIPTION = range(1)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Сгенерировать объявления", callback_data='generate')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """Привет! Я помогу тебе создать рекламные объявления для товаров или услуг.

Пожалуйста, укажи:
- Название товара или услуги
- Акции, бонусы или выгоды для покупателя
- Сайт продавца (если нужно)

Нажми кнопку ниже, чтобы начать:""",
        reply_markup=reply_markup
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Напиши, что ты продаёшь и какие акции, бонусы или преимущества есть:\n\nНапример: продажа лодок в Москве, скидка 20%"
    )
    return WAITING_DESCRIPTION

def generate_ads(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Ты создаёшь продающие объявления. Каждое состоит из:\n- Заголовок 1: до 56 символов\n- Заголовок 2: до 30 символов\n- Текст: до 81 символа.\nОтвет всегда в виде трёх разных вариантов."},
                {"role": "user", "content": f"Создай объявления для: {prompt}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка при генерации: {e}"

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

async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("✏️ Хорошо, введи новое описание товара и акции.")
    return WAITING_DESCRIPTION

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот сброшен. Напиши /start, чтобы начать заново 🔁")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_button, pattern='^generate$'))
    app.add_handler(CallbackQueryHandler(handle_button, pattern='^regenerate$'))
    app.add_handler(CallbackQueryHandler(handle_edit, pattern='^edit$'))

    print("🚀 Бот запущен и готов к работе")
    app.run_polling()
