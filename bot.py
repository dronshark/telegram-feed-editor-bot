import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from openai import OpenAI
from lxml import etree

# Состояния диалога
WAITING_FILE, CHOOSE_ACTION = range(2)

# Инициализация OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот для редактирования товарных фидов.\nЗагрузи XML/CSV файл, и я помогу с ним работать.")
    return WAITING_FILE

# Получаем файл от пользователя
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    file_name = file.file_name
    file_path = f"temp/{file_name}"

    await file.get_file().download_to_drive(file_path)
    context.user_data["file_path"] = file_path

    keyboard = [
        [InlineKeyboardButton("Изменить цены", callback_data='price')],
        [InlineKeyboardButton("Обновить картинки", callback_data='picture')],
        [InlineKeyboardButton("Сгенерировать описания", callback_data='description')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Файл получен. Что будем делать?", reply_markup=reply_markup)
    return CHOOSE_ACTION

# Генерация описания через GPT
def generate_description_via_gpt(name):
    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "Ты пишешь краткие описания товаров (до 80 символов), включая название и мотивацию купить на сайте polza.ru."},
                {"role": "user", "content": f"Сгенерируй описание для товара: {name}"}
            ]
        )
        return completion.choices[0].message.content[:81].strip()
    except Exception as e:
        return "Покупайте на сайте polza.ru — качество и бонусы!"

# Обработка выбора действия
async def process_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data
    file_path = context.user_data.get("file_path")

    if action == "description":
        tree = etree.parse(file_path)
        root = tree.getroot()

        for offer in root.xpath(".//offer"):
            name = offer.findtext("name", default="Товар")
            description = generate_description_via_gpt(name)
            desc_elem = offer.find("description")
            if desc_elem is not None:
                desc_elem.text = description
            else:
                etree.SubElement(offer, "description").text = description

        file_path = file_path.replace(".xml", "_desc.xml")
        tree.write(file_path, encoding="utf-8", xml_declaration=True, pretty_print=True)
        context.user_data["file_path"] = file_path
        await query.edit_message_text("Описания сгенерированы через GPT 🧠")
    else:
        await query.edit_message_text("Действие пока не реализовано (в этом примере)")

    await query.message.reply_document(InputFile(file_path), caption="Вот ваш обновлённый фид")
    return ConversationHandler.END

# Сброс
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Окей, если что — напиши /start заново 😊")
    return ConversationHandler.END

# Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FILE: [MessageHandler(filters.Document.ALL, handle_file)],
            CHOOSE_ACTION: [CallbackQueryHandler(process_action)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    print("🤖 Бот запущен с интерфейсом для работы с фидами")
    app.run_polling()
