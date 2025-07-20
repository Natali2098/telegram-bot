import logging
import os
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from dotenv import load_dotenv

# Стадії для розмови
NAME, PHONE, TYPE, SERVICE, ADDRESS, TIME, COMMENT, PHOTO = range(8)

# ID користувача, який отримає заявку
OWNER_ID = 7224980019  # заміни на свій Telegram ID

# Список послуг
services = {
    "Побутовий": [
        "Антибактеріальна чистка",
        "Ремонт",
        "Заправка",
        "Монтаж/демонтаж",
        "Діагностика",
        "Інше"
    ],
    "Авто": [
        "Пошук витоків",
        "Ремонт",
        "Передсезонне обслуговування",
        "Заправка з у/ф барвником",
        "Інше"
    ]
}

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): 
    await update.message.reply_text(
        "Привіт! 👋 Я — Дмитро, ваш надійний майстер з обслуговування кондиціонерів в Одесі.\n"
        "Допоможу швидко, якісно та з гарантією. Напишіть, будь ласка, Ваше ім'я:"
    )
    return NAME

# Ім’я
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    context.user_data["name"] = name

    keyboard = [["Побутовий", "Авто"]]

    await update.message.reply_text(
        f"Приємно познайомитись, {name}! 👋\n\n"
        "З яким типом кондиціонера виникла потреба? 👇\n"
        "Оберіть один із варіантів нижче:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return TYPE

# Тип кондиціонера
async def get_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    type_selected = update.message.text.strip().capitalize()
    if type_selected not in services:
        await update.message.reply_text("⚠️ Будь ласка, оберіть один із варіантів з клавіатури.")
        return TYPE

    context.user_data["type"] = type_selected
    buttons = [[s] for s in services[type_selected]]
    await update.message.reply_text(
        "🔧 Дякую!\nОберіть, будь ласка, послугу, яка Вас цікавить:",
        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return SERVICE

# Послуга
async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service"] = update.message.text
    await update.message.reply_text(
        "📞 Тепер, будь ласка, залиште номер телефону для зв’язку.\n"
        "Я зателефоную або напишу Вам для уточнення деталей.")
    return PHONE

# Телефон
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("📍 Залиште, будь ласка, адресу або назву району, де потрібно виконати роботу.")
    return ADDRESS

# Адреса
async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    await update.message.reply_text("🕒 Коли Вам зручно, щоб я приїхав? Вкажіть день і бажаний час.")
    return TIME

# Час
async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["time"] = update.message.text

    skip_keyboard = [["Пропустити"]]
    await update.message.reply_text(
        "💬 Якщо є додаткові побажання чи деталі — напишіть їх тут.\n"
        "Якщо нічого не потрібно — натисніть кнопку «Пропустити».",
        reply_markup=ReplyKeyboardMarkup(skip_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return COMMENT

# Коментар
async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    if text == "пропустити":
        context.user_data["comment"] = "-"
    else:
        context.user_data["comment"] = update.message.text

    skip_keyboard = [["Пропустити"]]
    await update.message.reply_text(
        "📸 За бажанням, можете надіслати фото проблеми або кондиціонера. Це допоможе мені краще підготуватися.\n\n"
        "Якщо фото немає — натисніть «Пропустити».",
        reply_markup=ReplyKeyboardMarkup(skip_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PHOTO

# Фото або пропуск
async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.photo:
        context.user_data["photo"] = update.message.photo[-1].file_id
    elif update.message and update.message.text and update.message.text.strip().lower() == "пропустити":
        context.user_data["photo"] = None
    else:
        await update.message.reply_text("Будь ласка, надішліть фото або натисніть «Пропустити».")
        return PHOTO

    text = (
        f"🔧 Нова заявка:\n"
        f"👤 Ім’я: {context.user_data['name']}\n"
        f"📞 Телефон: {context.user_data['phone']}\n"
        f"❄️ Тип: {context.user_data['type']}\n"
        f"🔧 Послуга: {context.user_data['service']}\n"
        f"📍 Адреса: {context.user_data['address']}\n"
        f"🕐 Час: {context.user_data['time']}\n"
        f"💬 Коментар: {context.user_data['comment']}"
    )

    await context.bot.send_message(chat_id=OWNER_ID, text=text)

    if context.user_data["photo"]:
        await context.bot.send_photo(chat_id=OWNER_ID, photo=context.user_data["photo"])

    await update.message.reply_text(
        "✅ Дякую! Заявку отримано.\n"
        "Я зв'яжусь із вами найближчим часом, щоб підтвердити деталі та домовитись про зручний час.\n\n"
        "Хорошого дня! 😊",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# Скасування
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заявку скасовано.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Логування помилок
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"❌ Exception: {context.error}")

# Запуск бота
def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("❌ Помилка: токен не знайдено в .env файлі")
        return

    app = ApplicationBuilder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_type)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_time)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            PHOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv)
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()