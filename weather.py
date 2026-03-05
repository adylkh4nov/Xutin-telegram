import locale
import datetime
import warnings
import requests
from datetime import datetime as d
from config import weather_token

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Поддержка русской локали на Windows и Linux
for _loc in ('ru_RU.UTF-8', 'ru_RU', 'Russian_Russia.1251', 'ru'):
    try:
        locale.setlocale(locale.LC_TIME, _loc)
        break
    except locale.Error:
        continue


def get_weather(city: str) -> str:
    try:
        r = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={
                'q': city,
                'appid': weather_token,
                'units': 'metric',
                'lang': 'ru',
            },
            verify=False,
            timeout=10,
        )
        data = r.json()

        if data.get('cod') != 200:
            return f'Город "{city}" не найден. Проверьте название.'

        city_name       = data['name']
        cur_weather     = int(data['main']['temp'])
        feels_like      = int(data['main']['feels_like'])
        description     = data['weather'][0]['description']
        humidity        = data['main']['humidity']
        wind            = data['wind']['speed']
        sunrise         = datetime.datetime.fromtimestamp(data['sys']['sunrise'])
        sunset          = datetime.datetime.fromtimestamp(data['sys']['sunset'])
        length_day      = sunset - sunrise
        date            = d.now().strftime('%d %B %Y')

        return (
            f'🌍 *Погода в {city_name}* на {date}\n\n'
            f'🌡 Температура: {cur_weather} °C\n'
            f'🤔 Ощущается как: {feels_like} °C\n'
            f'☁️ {description.capitalize()}\n'
            f'💧 Влажность: {humidity}%\n'
            f'💨 Ветер: {wind} м/с\n'
            f'🌅 Восход: {sunrise.strftime("%H:%M")}\n'
            f'🌇 Закат: {sunset.strftime("%H:%M")}\n'
            f'⏱ Длина дня: {str(length_day)[:-3]}'
        )

    except requests.exceptions.RequestException as e:
        return f'Ошибка сети: {e}'
    except Exception as e:
        return 'Не удалось получить погоду. Проверьте название города.'
