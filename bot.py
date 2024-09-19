import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler  # Импортируем CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random

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

# Словарь с именами и user_id
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

# Функция для генерации покерных карт
def generate_hand():
    suits = ['♠', '♣', '♦', '♥']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [f'{rank}{suit}' for suit in suits for rank in ranks]
    random.shuffle(deck)
    return [deck.pop(), deck.pop()]

def evaluate_hand(cards):
    ranks = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
             'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    hand = sorted(cards, key=lambda card: ranks[card[:-1]], reverse=True)
    return hand

# Команда "start"
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь /dolgi, чтобы получить список задолжников.')

# Команда "dolgi"
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
        message = "Нет задолженностей"

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
                message += f"{name}, {phone}, {bank}, {amount} \n"
        except ValueError:
            # Если значение не является числом, пропустить его
            continue

    if message == "КОМУ ПЕРЕВОДИТЬ 💸\n\n":
        message = "Нет плюсовых игроков"

    await update.message.reply_text(message, parse_mode='HTML')

# Команда "ruletka"
async def ruletka(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Участвую", callback_data='join')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Нажмите кнопку, чтобы участвовать в рулетке!', reply_markup=reply_markup)

# Обработчик нажатий на кнопки
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user

    if 'players' not in context.chat_data:
        context.chat_data['players'] = []

    if len(context.chat_data['players']) < 2:
        if user.id not in context.chat_data['players']:
            context.chat_data['players'].append(user.id)
            await query.answer()
            await query.edit_message_text(text=f"Вы добавлены в очередь. ({len(context.chat_data['players'])}/2)")
        else:
            await query.answer("Вы уже участвуете в рулетке.")
    else:
        await query.answer("Рулетка уже запущена. Подождите окончания текущего раунда.")

    if len(context.chat_data['players']) == 2:
        player1 = context.chat_data['players'][0]
        player2 = context.chat_data['players'][1]

        # Розыгрыш карт
        hand1 = generate_hand()
        hand2 = generate_hand()
        community_cards = [generate_hand() for _ in range(5)]

        # Подготовка сообщений
        messages = []
        messages.append(f"Карманные карты:\nИгрок 1: {hand1}\nИгрок 2: {hand2}\n")
        messages.append(f"Флоп: {community_cards[0]}\n")
        messages.append(f"Терн: {community_cards[1]}\n")
        messages.append(f"Ривер: {community_cards[2]}\n")
        
        # Объявление победителя (Пример, не реализован настоящий алгоритм оценки рук)
        winner = random.choice([player1, player2])
        messages.append(f"Победитель: {winner} с комбинацией {evaluate_hand(hand1 + community_cards) if winner == player1 else evaluate_hand(hand2 + community_cards)}")

        for msg in messages:
            await update.message.reply_text(msg)

        # Очистка данных после завершения раунда
        context.chat_data['players'] = []

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dolgi", get_debts))
    application.add_handler(CommandHandler("komu_kidat", komu_kidat))
    application.add_handler(CommandHandler("ruletka", ruletka))
    application.add_handler(CallbackQueryHandler(button))

    # Запуск бота
    application.run_poll
