import telebot
import psycopg2
from telebot import types


conn = psycopg2.connect(
    dbname="beauty",
    user="postgres",
    password="12345aA",
    host="localhost",
    port="5432"
)



cursor = conn.cursor()


BOT_TOKEN = '6933645493:AAGopjAL-SyZsZe4nD-tkh7EXvDpGR9obW8'


bot = telebot.TeleBot(BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('🗓Записаться', callback_data='book')
    btn2 = types.InlineKeyboardButton('📢О нас', callback_data='about')
    btn3 = types.InlineKeyboardButton('💳Прайс-лист', callback_data='price')
    btn4 = types.InlineKeyboardButton('❌Отмена записи', callback_data='cancel')
    markup.add(btn1, btn2, btn3, btn4)

    photo_url = 'https://i.pinimg.com/564x/07/59/bc/0759bc346e180e0f87c78c8bba14fd55.jpg'
    photo_message = bot.send_photo(message.chat.id, photo_url, caption='Добро пожаловать в салон парикмахерских услуг Timeless Beauty Club!\nЧем могу вам помочь?', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def price_callback(call):
    bot.send_message(call.message.chat.id, 'Введите ваш номер телефона для поиска записи')
    bot.register_next_step_handler(call.message, phone_cancel)

def phone_cancel(message):
    phone_number = message.text
    cursor.execute("SELECT phone FROM appointments WHERE phone = %s", (phone_number,))
    appointment = cursor.fetchone()

    if appointment:
        cursor.execute("DELETE FROM appointments WHERE phone = %s", (appointment,))
        conn.commit()
        bot.send_message(message.chat.id, "Ваша запись успешно удалена!")
    else:
        bot.send_message(message.chat.id, "Запись с таким номером телефона не найдена")

@bot.callback_query_handler(func=lambda call: call.data == 'about')
def about_callback(call):
        markup = types.InlineKeyboardMarkup(row_width=2)
        button = types.InlineKeyboardButton("Геопозиция", callback_data='geo')
        button1 = types.InlineKeyboardButton("Вконтакте", url='https://vk.com/public211313306')
        markup.add(button,button1)
        bot.send_message(call.message.chat.id, "Наш салон предлагает широкий спектр услуг по уходу за волосами. Мы работаем с опытными стилистами и используем только качественные продукты.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'price')
def price_callback(call):
    photo_url = 'https://i.pinimg.com/564x/09/61/fa/0961fa4c914fc90403c744ba1ff399c5.jpg'
    photo_message = bot.send_photo(call.message.chat.id, photo_url, caption='Вот наш актуальный прайс-лист!')

@bot.callback_query_handler(func=lambda call: call.data == 'menu')
def price_callback(call):
    start(call.message)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == 'book':
        bot.send_message(call.message.chat.id, 'Введите ваше имя:')
        bot.register_next_step_handler(call.message, get_name)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == 'geo':
        bot.send_location(call.message.chat.id, 59.923072, 30.412024)
def get_name(message):
    name = message.text
    bot.send_message(message.chat.id, "Введите ваш номер телефона:")
    bot.register_next_step_handler(message, get_phone, name)

def get_phone(message, name):
    phone = message.text

    cursor.execute("SELECT  name_hair FROM hairdressers")
    hairdressers = cursor.fetchall()

    markup = types.ReplyKeyboardMarkup(row_width=1)
    for hairdresser in hairdressers:
        button = types.KeyboardButton(hairdresser[0])
        markup.add(button)

    bot.send_message(message.chat.id, "Выберите парикмахера:", reply_markup=markup)
    bot.register_next_step_handler(message, select_hairdresser, name, phone)

def select_hairdresser(message, name, phone):
    selected_hairdresser = message.text

    cursor.execute(
        "SELECT ad.date FROM available_dates ad JOIN hairdressers hd ON ad.id_hair = hd.hairdresser_id WHERE hd.name_hair = %s group by ad.date",
        (selected_hairdresser,))
    available_dates = cursor.fetchall()

    markup = types.ReplyKeyboardMarkup(row_width=1)
    for date in available_dates:
        button = types.KeyboardButton(date[0])
        markup.add(button)

    bot.send_message(message.chat.id, "Выберите дату:", reply_markup=markup)
    bot.register_next_step_handler(message, select_date, name, phone, selected_hairdresser)

def select_date(message, name, phone, selected_hairdresser):
    selected_date = message.text

    cursor.execute("SELECT ad.time FROM available_dates ad JOIN hairdressers hd ON ad.id_hair = hd.hairdresser_id WHERE hd.name_hair = %s and ad.date = %s",
        (selected_hairdresser, selected_date))
    available_times = cursor.fetchall()

    markup = types.ReplyKeyboardMarkup(row_width=2)
    for time in available_times:
        button = types.KeyboardButton(time[0])
        markup.add(button)

    bot.send_message(message.chat.id, "Выберите время:", reply_markup=markup)
    bot.register_next_step_handler(message, make_appointment, name, phone, selected_hairdresser, selected_date)

def delete_date_time_from_available_dates(selected_date, selected_time):
    query = f"DELETE FROM available_dates WHERE date = '{selected_date}' AND time = '{selected_time}';"
    cursor.execute(query)
    conn.commit()

def make_appointment(message, name, phone, selected_hairdresser, selected_date):
    selected_time = message.text
    delete_date_time_from_available_dates(selected_date, selected_time)

    cursor.execute(
        "INSERT INTO appointments (name, phone, name_hair, date, time) VALUES (%s, %s, %s, %s, %s)",
        (name, phone, selected_hairdresser, selected_date, selected_time))
    conn.commit()

    bot.send_message(message.chat.id, "Запись успешно добавлена!\nСкоро мы свяжемся с вами по номеру телефона для подтверждения записи!",reply_markup=types.ReplyKeyboardRemove())

    markup = types.InlineKeyboardMarkup(row_width=1)
    button = types.InlineKeyboardButton("🔙Меню", callback_data='menu')
    markup.add(button)
    bot.send_message(message.chat.id, "Вернуться в главное меню", reply_markup=markup)


bot.polling()

