import sqlite3
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота (замените на свой)
BOT_TOKEN = "8317804259:AAEO9qDyU3AqPv6LrBwN1I-ebJf4hQwR4eg"


# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        full_name TEXT,
        group_name TEXT,
        registration_date TEXT,
        points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1
    )
    ''')

    # Таблица достижений
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        achievement_type TEXT,
        description TEXT,
        points_awarded INTEGER,
        status TEXT DEFAULT 'pending',
        submission_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Таблица покупок
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        item_name TEXT,
        item_price INTEGER,
        purchase_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()


# Функции для работы с базой данных
def get_user(telegram_id):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def register_user(telegram_id, username, full_name, group_name):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
    INSERT INTO users (telegram_id, username, full_name, group_name, registration_date)
    VALUES (?, ?, ?, ?, ?)
    ''', (telegram_id, username, full_name, group_name, registration_date))
    conn.commit()
    conn.close()


def update_user_points(telegram_id, points):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ? WHERE telegram_id = ?', (points, telegram_id))

    # Обновление уровня (1 уровень за каждые 100 очков)
    cursor.execute('UPDATE users SET level = (points / 100) + 1 WHERE telegram_id = ?', (telegram_id,))

    conn.commit()
    conn.close()


def add_achievement(user_id, achievement_type, description):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    submission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Определяем количество очков в зависимости от типа достижения
    points_map = {
        'грамота': 50,
        'сертификат': 30,
        'диплом': 70,
        'благодарность': 20,
        'участие': 10
    }

    points = points_map.get(achievement_type.lower(), 10)

    cursor.execute('''
    INSERT INTO achievements (user_id, achievement_type, description, points_awarded, submission_date)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, achievement_type, description, points, submission_date))

    conn.commit()
    conn.close()
    return points


def get_user_achievements(user_id):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM achievements WHERE user_id = ?', (user_id,))
    achievements = cursor.fetchall()
    conn.close()
    return achievements


def add_purchase(user_id, item_name, item_price):
    conn = sqlite3.connect('students.db')
    cursor = conn.cursor()
    purchase_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
    INSERT INTO purchases (user_id, item_name, item_price, purchase_date)
    VALUES (?, ?, ?, ?)
    ''', (user_id, item_name, item_price, purchase_date))

    cursor.execute('UPDATE users SET points = points - ? WHERE id = ?', (item_price, user_id))

    conn.commit()
    conn.close()


# Магазин товаров
SHOP_ITEMS = [
    {"name": "Футболка с арнаментом", "price": 200, "description": "Стильная футболка с логотипом колледжа"},
    {"name": "Блокнот", "price": 100, "description": "Качественный блокнот для записей"},
    {"name": "Брелок", "price": 50, "description": "Красивый брелок с символикой"},
    {"name": "Ручка", "price": 30, "description": "Удобная ручка с логотипом"},
    {"name": "Толстовка", "price": 300, "description": "Теплая толстовка с дизайном колледжа"}
]


# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    # Проверяем, зарегистрирован ли пользователь
    existing_user = get_user(telegram_id)

    if existing_user:
        # Пользователь уже зарегистрирован
        keyboard = [
            ["Добавить достижение"],
            ["Мои баллы", "Мой уровень"],
            ["Магазин", "Мои покупки"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"Добро пожаловать обратно, {existing_user[3]}! 🎓\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    else:
        # Новый пользователь
        keyboard = [["Зарегистрироваться"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "👋 Привет! Я бот для учета достижений студентов.\n"
            "Для начала работы необходимо зарегистрироваться.",
            reply_markup=reply_markup
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    telegram_id = user.id

    existing_user = get_user(telegram_id)

    if text == "Зарегистрироваться":
        if existing_user:
            await update.message.reply_text("Вы уже зарегистрированы!")
            return

        # Сохраняем состояние для регистрации
        context.user_data['awaiting_registration'] = True
        await update.message.reply_text(
            "Для регистрации введите ваши данные в формате:\n"
            "ФИО, Группа\n\n"
            "Например: Иванов Иван Иванович, ИСП-21"
        )

    elif 'awaiting_registration' in context.user_data:
        try:
            full_name, group_name = text.split(',', 1)
            full_name = full_name.strip()
            group_name = group_name.strip()

            register_user(telegram_id, user.username, full_name, group_name)
            del context.user_data['awaiting_registration']

            keyboard = [
                ["Добавить достижение"],
                ["Мои баллы", "Мой уровень"],
                ["Магазин", "Мои покупки"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"🎉 Регистрация завершена, {full_name}!\n"
                "Теперь вы можете добавлять свои достижения.",
                reply_markup=reply_markup
            )
        except:
            await update.message.reply_text(
                "Неверный формат. Пожалуйста, введите данные в формате:\n"
                "ФИО, Группа\n\n"
                "Например: Иванов Иван Иванович, ИСП-21"
            )

    elif text == "Добавить достижение":
        if not existing_user:
            await update.message.reply_text("Сначала необходимо зарегистрироваться!")
            return

        context.user_data['awaiting_achievement'] = True
        await update.message.reply_text(
            "📝 Введите ваше достижение в формате:\n"
            "Тип: Описание\n\n"
            "Доступные типы: Грамота, Сертификат, Диплом, Благодарность, Участие\n\n"
            "Пример: Грамота: 1 место в олимпиаде по программированию"
        )

    elif 'awaiting_achievement' in context.user_data:
        if not existing_user:
            await update.message.reply_text("Сначала необходимо зарегистрироваться!")
            return

        try:
            achievement_type, description = text.split(':', 1)
            achievement_type = achievement_type.strip()
            description = description.strip()

            points = add_achievement(existing_user[0], achievement_type, description)

            del context.user_data['awaiting_achievement']

            await update.message.reply_text(
                f"✅ Достижение добавлено!\n"
                f"Тип: {achievement_type}\n"
                f"Описание: {description}\n"
                f"Начислено баллов: {points}\n\n"
                f"Администратор проверит ваше достижение и подтвердит его."
            )
        except:
            await update.message.reply_text(
                "Неверный формат. Пожалуйста, введите достижение в формате:\n"
                "Тип: Описание\n\n"
                "Пример: Грамота: 1 место в олимпиаде по программированию"
            )

    elif text == "Мои баллы":
        if not existing_user:
            await update.message.reply_text("Сначала необходимо зарегистрироваться!")
            return

        await update.message.reply_text(
            f"💰 Ваши баллы: {existing_user[6]}\n\n"
            f"Вы можете потратить их в магазине или продолжать зарабатывать!"
        )

    elif text == "Мой уровень":
        if not existing_user:
            await update.message.reply_text("Сначала необходимо зарегистрироваться!")
            return

        await update.message.reply_text(
            f"🏆 Ваш уровень: {existing_user[7]}\n"
            f"Баллы до следующего уровня: {100 - (existing_user[6] % 100)}"
        )

    elif text == "Магазин":
        if not existing_user:
            await update.message.reply_text("Сначала необходимо зарегистрироваться!")
            return

        keyboard = []
        for item in SHOP_ITEMS:
            keyboard.append([InlineKeyboardButton(
                f"{item['name']} - {item['price']} баллов",
                callback_data=f"buy_{item['name']}"
            )])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🛍️ Магазин мерча:\n\n" +
            "\n".join([f"• {item['name']} - {item['price']} баллов ({item['description']})"
                       for item in SHOP_ITEMS]) +
            f"\n\nВаш баланс: {existing_user[6]} баллов",
            reply_markup=reply_markup
        )

    elif text == "Мои покупки":
        if not existing_user:
            await update.message.reply_text("Сначала необходимо зарегистрироваться!")
            return

        conn = sqlite3.connect('students.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM purchases WHERE user_id = ? ORDER BY purchase_date DESC', (existing_user[0],))
        purchases = cursor.fetchall()
        conn.close()

        if not purchases:
            await update.message.reply_text("У вас пока нет покупок.")
        else:
            purchases_text = "🛒 Ваши покупки:\n\n"
            for purchase in purchases:
                purchases_text += f"• {purchase[2]} - {purchase[3]} баллов ({purchase[4]})\n"

            await update.message.reply_text(purchases_text)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith('buy_'):
        item_name = query.data[4:]
        user = get_user(update.effective_user.id)

        if not user:
            await query.edit_message_text("Ошибка: пользователь не найден")
            return

        # Находим товар
        item = next((i for i in SHOP_ITEMS if i['name'] == item_name), None)

        if not item:
            await query.edit_message_text("Товар не найден")
            return

        if user[6] < item['price']:
            await query.edit_message_text(
                f"❌ Недостаточно баллов!\n"
                f"Цена: {item['price']} баллов\n"
                f"Ваш баланс: {user[6]} баллов"
            )
            return

        # Совершаем покупку
        add_purchase(user[0], item['name'], item['price'])

        await query.edit_message_text(
            f"🎉 Покупка совершена!\n"
            f"Товар: {item['name']}\n"
            f"Цена: {item['price']} баллов\n"
            f"Новый баланс: {user[6] - item['price']} баллов\n\n"
            f"Обратитесь к администратору для получения товара."
        )


# Основная функция
def main():
    # Инициализация базы данных
    init_db()

    # Создание приложения
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Запуск бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()