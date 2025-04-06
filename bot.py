import os
import openai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from telegram.ext import Updater
from telegram.error import Conflict

# Состояния
WAITING_DESCRIPTION = range(1)

# Инициализация OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

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

# Генерация объявлений через GPT-4 Turbo
def generate_ads(prompt):
    try:
        # Запрос к OpenAI для генерации объявлений
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Ты создаёшь продающие объявления. Каждое состоит из:\n- Заголовок 1: до 56 символов\n- Заголовок 2: до 30 символов\n- Текст: до 81 символа.\nОтвет всегда в виде трёх разных вариантов."},
                {"role": "user", "content": f"Создай объявления для: {prompt}"}
            ]
        )
        ads = response['choices'][0]['message']['content'].strip()
        
        # Проверка на корректность возвращаемого ответа
        if not ads:
            return "Не удалось сгенерировать объявления. Попробуйте снова."
        return ads
    except Exception as e:
        return f"Ошибка при генерации: {e}"

# Получение описания и генерация
async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    await update.message.reply_text("🔧 Генерирую объявления, подожди пару секунд...")
    ads = generate_ads(prompt)
    
    # Если произошла ошибка при генерации
    if "Ошибка" in ads:
        await update.message.reply_text(ads)
    else:
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

# Функция для настройки webhook
async def set_webhook():
    url = os.getenv("WEBHOOK_URL")
    await app.bot.set_webhook(url)

# Запуск с webhook
def main():
    token = os.getenv("BOT_TOKEN")
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

    print("🚀 Бот запущен с webhook")
    
    # Настроим webhook
    asyncio.run(set_webhook())
    
    # Запуск с webhook
    app.run_webhook(listen="0.0.0.0", port=5000, url_path=os.getenv("BOT_TOKEN"))
    
if __name__ == "__main__":
    main()
