import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random
import time

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

# Хранилище участников рулетки
roulette_participants = []

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
        message = "Нет задолженностей"

    await update.message.reply_text(message, parse_mode='HTML')

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

async def ruletka(update: Update, context: CallbackContext) -> None:
    global roulette_participants
    roulette_participants = []

    keyboard = [[InlineKeyboardButton("Принять участие", callback_data='join')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        'Принять участие в рулетке', 
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    
    if len(roulette_participants) >= 2:
        await query.answer(text="Участников уже достаточно.")
        return
    
    if user.id not in [p['id'] for p in roulette_participants]:
        roulette_participants.append({'id': user.id, 'name': user.full_name})
        await query.answer(text="Вы приняли участие!")
    
    if len(roulette_participants) == 2:
        context.job_queue.run_once(start_roulette, 1, context=update.message.chat_id)

async def start_roulette(context: CallbackContext) -> None:
    chat_id = context.job.context
    if len(roulette_participants) < 2:
        await context.bot.send_message(chat_id, "Недостаточно участников для игры.")
        return
    
    # Создаем колоду и раздаем карты
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = [f'{rank}{suit}' for suit in suits for rank in ranks]
    random.shuffle(deck)

    def deal_hand():
        return [deck.pop(), deck.pop()]

    def hand_strength(hand):
        # Простой пример: вернуть случайное число для оценки силы руки
        return random.randint(1, 100)

    player1_hand = deal_hand()
    player2_hand = deal_hand()
    
    message = f"Участвуют:\n1. {roulette_participants[0]['name']} {user_ids.get(roulette_participants[0]['name'], '')}\n2. {roulette_participants[1]['name']} {user_ids.get(roulette_participants[1]['name'], '')}\n\n"

    message += "Карманные карты:\n"
    message += f"1. {roulette_participants[0]['name']}: {', '.join(player1_hand)}\n"
    message += f"2. {roulette_participants[1]['name']}: {', '.join(player2_hand)}\n"

    await context.bot.send_message(chat_id, message)

    time.sleep(5)
    flop = [deck.pop() for _ in range(3)]
    await context.bot.send_message(chat_id, f"Флоп: {', '.join(flop)}")

    time.sleep(5)
    turn = deck.pop()
    await context.bot.send_message(chat_id, f"Терн: {turn}")

    time.sleep(5)
    river = deck.pop()
    await context.bot.send_message(chat_id, f"Ривер: {river}")

    # Определение победителя
    player1_strength = hand_strength(player1_hand + flop + [turn, river])
    player2_strength = hand_strength(player2_hand + flop + [turn, river])
    
    if player1_strength > player2_strength:
        winner = roulette_participants[0]['name']
    elif player2_strength > player1_strength:
        winner = roulette_participants[1]['name']
    else:
        winner = "Ничья"

    await context.bot.send_message(chat_id, f"Победитель: {winner}")

def main() -> None:
    global application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dolgi", get_debts))
    application.add_handler(CommandHandler("komu_kidat", komu_kidat))
    application.add_handler(CommandHandler("ruletka", ruletka))
    application.add_handler(CallbackQueryHandler(button))
    
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
