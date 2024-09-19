import logging
import nest_asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
from collections import namedtuple
from oauth2client.service_account import ServiceAccountCredentials
import gspread
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

# Глобальные переменные
participants = []
MAX_PARTICIPANTS = 2

Card = namedtuple('Card', ['suit', 'rank'])

# Колода карт
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
deck = [Card(suit, rank) for suit in SUITS for rank in RANKS]

# Определение комбинаций в покере
def hand_rank(hand):
    """Возвращает числовое значение руки для упрощенного сравнения рук."""
    values = sorted(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'].index(card.rank) for card in hand], reverse=True)
    suits = [card.suit for card in hand]
    is_flush = len(set(suits)) == 1
    is_straight = values == list(range(values[0], values[0] - 5, -1))
    if values == [12, 3, 2, 1, 0]:  # Особый случай для стрита до туза
        values = [4, 3, 2, 1, 0]
    counts = {value: values.count(value) for value in values}
    if is_straight and is_flush:
        return (8, values)
    elif 4 in counts.values():
        return (7, counts)
    elif 3 in counts.values() and 2 in counts.values():
        return (6, counts)
    elif is_flush:
        return (5, values)
    elif is_straight:
        return (4, values)
    elif 3 in counts.values():
        return (3, counts)
    elif list(counts.values()).count(2) == 2:
        return (2, counts)
    elif 2 in counts.values():
        return (1, counts)
    else:
        return (0, values)

def get_winner(hands):
    """Определяет победителя из списка рук на основе комбинации."""
    ranked_hands = [(hand_rank(hand), hand) for hand in hands]
    ranked_hands.sort(reverse=True)
    return ranked_hands[0]

# Функции для работы с долгами и переведением
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
                message += f"{name}, {phone}, {bank}, {amount} \n"
        except ValueError:
            # Если значение не является числом, пропустить его
            continue

    if message == "КОМУ ПЕРЕВОДИТЬ 💸\n\n":
        message = "Нет плюсовых игроков"

    await update.message.reply_text(message, parse_mode='HTML')

# Функции для рулетки
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Принять участие в рулетке", callback_data='register')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Принять участие в рулетке:', reply_markup=reply_markup)

async def register_for_roulette(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    if user.id in [p['id'] for p in participants]:
        await query.answer('Вы уже зарегистрированы.')
        return

    if len(participants) < MAX_PARTICIPANTS:
        participants.append({'id': user.id, 'name': user.username})
        await query.answer('Вы успешно зарегистрированы! 🎉')
        if len(participants) == MAX_PARTICIPANTS:
            # Запускаем раздачу после регистрации двух участников
            await start_roulette(update, context)
    else:
        await query.answer('Регистрация уже закрыта.')

async def start_roulette(update: Update, context: CallbackContext) -> None:
    # Убедимся, что раздача начинается только после регистрации двух участников
    if len(participants) < MAX_PARTICIPANTS:
        return

    # Выводим список участников
    participants_names = ", ".join([f"@{p['name']}" for p in participants])
    message = f"Участники: {participants_names}\n\nРаздача карт начинается! 🎲"
    await update.message.reply_text(message)

    # Перемешиваем колоду и раздаем по две карты каждому участнику
    random.shuffle(deck)
    hands = {p['id']: [deck.pop(), deck.pop()] for p in participants}

    # Для имитации раздачи и определения победителя
    flop = [deck.pop() for _ in range(3)]
    turn = deck.pop()
    river = deck.pop()

    def format_hand(hand):
        return ' '.join(f"{card.rank}{card.suit}" for card in hand)

    # Объявляем карты
    hand_messages = [f"@{p['name']} получил {format_hand(hand)}" for p, hand in zip(participants, hands.values())]
    await update.message.reply_text("\n".join(hand_messages))

    # Показываем флоп, терн и ривер
    await update.message.reply_text(f"Флоп: {format_hand(flop)}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Терн: {format_hand([turn])}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ривер: {format_hand([river])}")

    # Определяем победителя
    all_hands = [hand + flop + [turn, river] for hand in hands.values()]
    winner = get_winner(all_hands)
    winner_index = all_hands.index(winner[1])
    winner_name = participants[winner_index]['name']
    hand_description = format_hand(winner[1])
    await update.message.reply_text(f"🏆 Победитель: @{winner_name}\nКомбинация: {hand_description}")

def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("dolgi", get_debts))
    application.add_handler(CommandHandler("komu_kidat", komu_kidat))
    application.add_handler(CallbackQueryHandler(register_for_roulette, pattern='register'))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
