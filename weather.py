import locale
from datetime import datetime as d
import datetime
from config import weather_token
import requests
def weather(city,weather_token):
    try:
        r = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_token}&units=metric&lang=ru'
        )
        data = r.json()
        print(data)
        city = data["name"]
        cur_weather = int(data["main"]["temp"])
        feels_like = int(data["main"]["feels_like"])
        weather = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind = data["wind"]["speed"]
        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])
        locale.setlocale(locale.LC_TIME, "ru")
        now = d.now()
        date = now.strftime("%d %B %Y")
        length_day = datetime.datetime.fromtimestamp(data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        return(f' Погода в городе: {city} на {date}, \n Температура: {cur_weather} °C,\n Ощущается как: {feels_like} °C,\n Погода: {weather},\n'
              f' Влажность: {humidity} %,\n Ветер: {wind} м/c,\n Восход: {sunrise_timestamp},\n Закат: {sunset_timestamp},\n'
              f' Продолжительность дня: {length_day}')

    except Exception as e:
        print('Проверьте название города')
        print(e)

def main():
    city = input('Введите название города:')
    weather(city,weather_token)
