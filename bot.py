import os
import openai
import asyncio  # добавлен импорт asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
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
    except
