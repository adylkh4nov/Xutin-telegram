import datetime
import locale
from bot import bot
from telebot import types
import requests
import tenrgi
from datetime import datetime as d
from config import weather_token, claude_token
import anthropic


@bot.message_handler(commands=['start'])
def start(message):
    mess = f'Привет, {message.from_user.first_name}'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    Start = types.KeyboardButton('/start')
    News = types.KeyboardButton('/news')
    Weather = types.KeyboardButton('/weather')
    Claude = types.KeyboardButton('/Claude')
    markup.add(Start, News, Weather, Claude)
    bot.send_message(message.chat.id, mess, reply_markup=markup)


@bot.message_handler(commands=['news'])
def news(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        'Источник', url='https://tengrinews.kz/'))
    bot.send_message(message.chat.id, tenrgi.news, reply_markup=markup)


@bot.message_handler(commands=['weather'])
def weather(message):
    mesg = bot.reply_to(message, "Введите название города:")
    bot.register_next_step_handler(mesg, get_message)


def get_message(message):
    try:
        print(message.text)
        r = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={weather_token}&units=metric&lang=ru'
        )
        data = r.json()

        city = data["name"]
        cur_weather = int(data["main"]["temp"])
        feels_like = int(data["main"]["feels_like"])
        weather = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(
            data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(
            data["sys"]["sunset"])
        locale.setlocale(locale.LC_TIME, "ru")
        now = d.now()
        date = now.strftime("%d %B %Y")
        length_day = datetime.datetime.fromtimestamp(
            data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        bot.send_message(message.chat.id, f'  Погода в городе {city} на {date}, \n Температура: {cur_weather} °C,\n Ощущается как: {feels_like} °C,\n Погода: {weather},\n'
                         f' Влажность: {humidity} %,\n Ветер: {wind} м/c,\n Восход: {sunrise_timestamp},\n Закат: {sunset_timestamp},\n'
                         f' Продолжительность дня: {length_day}')

    except Exception as e:
        print(message)
        bot.send_message(message.chat.id, 'Проверьте название города')


def getChatMessage(message):
    print(message.from_user)
    client = anthropic.Anthropic(api_key=claude_token)
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": message.text}
        ]
    )
    bot.send_message(message.chat.id, response.content[0].text)


@bot.message_handler(commands=['Claude'])
def chat(message):
    mesg = bot.reply_to(message, "Введите текст для Claude")
    bot.register_next_step_handler(mesg, getChatMessage)
