import logging
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# Применение nest_asyncio для решения проблемы с циклом событий
nest_asyncio.apply()

# Используйте переменные окружения для токенов и идентификаторов
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
GOOGLE_CREDENTIALS = json.loads(os.getenv('GOOGLE_CREDENTIALS'))

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Настройка авторизации Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS, scope)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Словарь с именами и user_id (не будет использоваться в этой команде)
user_ids = {
    'Арсен': '@AKukhmazov',
    'Андрей Ж': '@zhandnab',
    'Андрей А': '@Alenin_Andrey',
    'Валера Б': '@valerkas',
    'Валера С': '@ValeriySark',
    'Зевс': '@Zeus7717',
    'Марат': '@Marat1k77',
    'Данзан': '@gunndanz',
    'Андрей С': '@Premove',
    'Евгений А': '@abram88',
    'Евгений М': '@Hate_m11',
    'Михаил Б': '@pryanni',
    'Костя': '@hlopkost',
    'Артем Г': '@Artem_Galaktionov22',
    'Борис': '@Pimienti',
    'Кирилл': '@Batko2003',
    'Егор': '@yagr55',
    'Влад': '@blvvld',
    'Мария': '@thaidancer',
    'Стас': '@s4fbrc4',
    'Имя1': '@user_id1',
    'Имя2': '@user_id2',
    # Добавьте другие имена и их user_id
}

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь /dolgi, чтобы получить список задолжников.')

async def get_debts(update: Update, context: CallbackContext) -> None:
    debts = sheet.row_values(560)  # Имена (строка 560)
    amounts = sheet.row_values(562)  # Долги (строка 562)

    message = "ДОЛГИ 🤡\n\n"
    for name, amount in zip(debts, amounts):
        if name == "Проверка":
            continue
        try:
            amount = int(amount.replace('\xa0', ''))  # Удалить неразрывные пробелы и преобразовать в целое число
            if amount < 0:
                if name in user_ids:
                    name = user_ids[name]  # Использовать user_id вместо имени
                message += f"{name} - {-amount}\n"
        except ValueError:
            # Если значение не является числом, пропустить его
            continue

    if message == "ДОЛГИ 🤡\n\n":
        message = "Нет задолженностей."

    await update.message.reply_text(message, parse_mode='HTML')

# Новая команда "komu_kidat"
async def komu_kidat(update: Update, context: CallbackContext) -> None:
    debts = sheet.row_values(560)  # Имена (строка 560)
    amounts = sheet.row_values(562)  # Долги (строка 562)
    phones = sheet.row_values(563)  # Номера телефонов (строка 563)
    banks = sheet.row_values(564)  # Банки (строка 564)

    message = "КОМУ ПЕРЕВОДИТЬ 💸\n\n"
    for name, amount, phone, bank in zip(debts, amounts, phones, banks):
        if name == "Проверка":
            continue
        try:
            amount = int(amount.replace('\xa0', ''))  # Удалить неразрывные пробелы и преобразовать в целое число
            if amount > 0:  # Включаем только тех, у кого положительные значения
                # Используем имя вместо user_id и добавляем сумму
                message += f"{name}, {phone}, {bank}, {amount} руб.\n"
        except ValueError:
            # Если значение не является числом, пропустить его
            continue

    if message == "КОМУ ПЕРЕВОДИТЬ 💸\n\n":
        message = "Нет данных для перевода."

    await update.message.reply_text(message, parse_mode='HTML')

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dolgi", get_debts))
    application.add_handler(CommandHandler("komu_kidat", komu_kidat))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
