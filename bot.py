import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from openai import OpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния
WAITING_DESCRIPTION = range(1)

# Инициализация OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Сгенерировать объявления", callback_data='generate')]]
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

# Обработка кнопки
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("""Напиши, что ты продаёшь и какие акции, бонусы или преимущества есть:

Например: продажа лодок в Москве, скидка 20%

Я сгенерирую три варианта объявлений. Погнали! 🚀""")
    return WAITING_DESCRIPTION

# Генерация через GPT-4 Turbo
def generate_ads(prompt):
    try:
        logger.info(f"Генерация объявления для запроса: {prompt}")
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Ты создаёшь продающие объявления. Каждое состоит из:\n- Заголовок 1: до 56 символов\n- Заголовок 2: до 30 символов\n- Текст: до 81 символа.\nОтвет всегда в виде трёх разных вариантов."},
                {"role": "user", "content": f"Создай объявления для: {prompt}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Ошибка OpenAI: {e}")
        return "⚠️ Произошла ошибка при генерации текста. Попробуй позже."

# Получение описания от пользователя
async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🛠 Создаю три варианта объявлений, подожди пару секунд...")
    ads = generate_ads(prompt)
    keyboard = [[InlineKeyboardButton("↺ Перегенерировать", callback_data='regenerate')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Вот 3 варианта:\n\n{ads}", reply_markup=reply_markup)
    await update.message.reply_text("Хочешь перегенерировать объявления? Отправь новое описание или нажми /start для сброса.")
    return WAITING_DESCRIPTION

# Сброс
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, если что — напиши /start заново 😊")
    await update.message.reply_text("Хочешь перегенерировать объявления? Отправь новое описание или нажми /start для сброса.")
    return WAITING_DESCRIPTION

# Запуск бота
if __name__ == "__main__":
    logger.info("Запуск Telegram-бота")

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN не найден в переменных окружения")

    app = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(handle_button))
    app.add_handler(CallbackQueryHandler(handle_button, pattern='^regenerate$'))

    logger.info("🤖 Бот для генерации рекламных объявлений запущен")
    app.run_polling()
