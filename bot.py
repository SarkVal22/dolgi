import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import random
import asyncio

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

# Функции для определения комбинаций покера
def rank_cards(hand):
    values = sorted(['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'].index(card[:-1]) for card in hand], reverse=True)
    suits = [card[-1] for card in hand]
    return values, suits

def is_flush(suits):
    return len(set(suits)) == 1

def is_straight(values):
    return values == list(range(values[0], values[0] - 5, -1))

def evaluate_hand(hand):
    values, suits = rank_cards(hand)
    if is_straight(values) and is_flush(suits):
        return "ROYAL FLUSH" if values[0] == 12 else "STRAIGHT FLUSH"
    if len(set(values)) == 2:
        return "FOUR OF A KIND" if values.count(values[0]) in [1, 4] else "FULL HOUSE"
    if is_flush(suits):
        return "FLUSH"
    if is_straight(values):
        return "STRAIGHT"
    if len(set(values)) == 3:
        return "THREE OF A KIND" if values.count(values[0]) in [1, 3] else "TWO PAIR"
    if len(set(values)) == 4:
        return "ONE PAIR"
    return "HIGH CARD"

def hand_strength(hand):
    return random.randint(1, 100)  # Для простоты, замените на реальную оценку

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Привет! Отправь /dolgi, чтобы получить список задолжников.')

async def get_debts(update: Update, context: CallbackContext) -> None:
    debts = sheet.row_values(560)  # Имена (строка 560)
    amounts = sheet.row_values(562)  # Долги (строка 562)

    message = "📉 ДОЛГИ 🤡\n\n"
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
            continue

    if message == "📉 ДОЛГИ 🤡\n\n":
        message = "Нет задолженностей"

    await update.message.reply_text(message, parse_mode='HTML')

async def komu_kidat(update: Update, context: CallbackContext) -> None:
    debts = sheet.row_values(560)  # Имена (строка 560)
    amounts = sheet.row_values(562)  # Долги (строка 562)
    phones = sheet.row_values(563)  # Номера телефонов (строка 563)
    banks = sheet.row_values(564)  # Банки (строка 564)

    message = "💸 КОМУ ПЕРЕВОДИТЬ 💸\n\n"
    for name, amount, phone, bank in zip(debts, amounts, phones, banks):
        if name == "Проверка":
            continue
        try:
            amount = int(amount.replace('\xa0', ''))  # Удалить неразрывные пробелы и преобразовать в целое число
            if amount > 0:  # Включаем только тех, у кого положительные значения
                message += f"{name}, {phone}, {bank}, {amount} \n"
        except ValueError:
            continue

    if message == "💸 КОМУ ПЕРЕВОДИТЬ 💸\n\n":
        message = "Нет плюсовых игроков"

    await update.message.reply_text(message, parse_mode='HTML')

async def ruletka(update: Update, context: CallbackContext) -> None:
    global roulette_participants
    roulette_participants = []

    keyboard = [[InlineKeyboardButton("Принять участие", callback_data='join')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        '🃏 Принять участие в рулетке 🃏', 
        reply_markup=reply_markup
    )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user

    logging.info(f"Button pressed by {user.id} ({user.full_name})")

    if len(roulette_participants) >= 2:
        await query.answer(text="🛑 Участников уже достаточно.")
        return
    
    if user.id not in [p['id'] for p in roulette_participants]:
        roulette_participants.append({'id': user.id, 'name': user.full_name})
        await query.answer(text="✅ Вы приняли участие!")

    logging.info(f"Current participants: {roulette_participants}")

    if len(roulette_participants) == 2:
        # Удаляем кнопку и сообщение о том, что участники записаны
        await query.message.edit_text(
            text=f"🎉 Участвуют:\n1. {roulette_participants[0]['name']} {user_ids.get(roulette_participants[0]['name'], '')}\n2. {roulette_participants[1]['name']} {user_ids.get(roulette_participants[1]['name'], '')}\n\n🚀 Начинаем раздачу...",
            reply_markup=None
        )

        # Создаем колоду и раздаем карты
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f'{rank}{suit}' for suit in suits for rank in ranks]
        random.shuffle(deck)

        def deal_hand():
            return [deck.pop(), deck.pop()]

        # Раздаем руки игрокам
        player1_hand = deal_hand()
        player2_hand = deal_hand()

        # Создаем флоп, терн и ривер
        community_cards = []
        for _ in range(3):
            community_cards.append(deck.pop())
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🃏 Флоп: {' '.join(community_cards)}"
        )
        await asyncio.sleep(5)

        community_cards.append(deck.pop())
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🃏 Тёрн: {' '.join(community_cards)}"
        )
        await asyncio.sleep(5)

        community_cards.append(deck.pop())
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🃏 Ривер: {' '.join(community_cards)}"
        )
        await asyncio.sleep(5)

        # Определяем победителя
        player1_hand += community_cards
        player2_hand += community_cards

        player1_hand_type = evaluate_hand(player1_hand)
        player2_hand_type = evaluate_hand(player2_hand)

        player1_strength = hand_strength(player1_hand)
        player2_strength = hand_strength(player2_hand)

        if player1_strength > player2_strength:
            winner = roulette_participants[0]
            winner_hand_type = player1_hand_type
        elif player1_strength < player2_strength:
            winner = roulette_participants[1]
            winner_hand_type = player2_hand_type
        else:
            winner = None
            winner_hand_type = "Ничья"

        if winner:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🏆 Победитель: {winner['name']} с комбинацией {winner_hand_type}!\n🃏 Руки:\n1. {player1_hand} (Игрок 1)\n2. {player2_hand} (Игрок 2)"
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🤝 Ничья! Руки:\n1. {roulette_participants[0]['name']}: {player1_hand}\n2. {roulette_participants[1]['name']}: {player2_hand}"
            )

        roulette_participants = []

def main() -> None:
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
