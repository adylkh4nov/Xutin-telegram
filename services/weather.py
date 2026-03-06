"""Получение прогноза погоды через OpenWeatherMap Forecast API."""
import html
import datetime
import warnings
import requests
from collections import defaultdict
from config import weather_token

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

_FORECAST_API = 'https://api.openweathermap.org/data/2.5/forecast'

_MONTHS = {
    1: 'января',   2: 'февраля',  3: 'марта',    4: 'апреля',
    5: 'мая',      6: 'июня',     7: 'июля',      8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября',   12: 'декабря',
}

_DAY_NAMES = {0: 'Пн', 1: 'Вт', 2: 'Ср', 3: 'Чт', 4: 'Пт', 5: 'Сб', 6: 'Вс'}

_ICON_MAP = {
    '01d': '☀️', '01n': '🌙',
    '02d': '⛅', '02n': '⛅',
    '03d': '🌥', '03n': '🌥',
    '04d': '☁️', '04n': '☁️',
    '09d': '🌧', '09n': '🌧',
    '10d': '🌦', '10n': '🌧',
    '11d': '⛈', '11n': '⛈',
    '13d': '❄️', '13n': '❄️',
    '50d': '🌫', '50n': '🌫',
}


def _icon(code: str) -> str:
    return _ICON_MAP.get(code, '🌡')


def _fetch_forecast(params: dict) -> dict | None:
    try:
        r = requests.get(_FORECAST_API, params={**params, 'cnt': 40,
            'appid': weather_token, 'units': 'metric', 'lang': 'ru'},
            verify=False, timeout=10)
        data = r.json()
        return data if str(data.get('cod')) == '200' else None
    except Exception:
        return None


# ──────────────── Single day forecast ────────────────

def _format_day(data: dict, day: str) -> str:
    city_name  = html.escape(data['city']['name'])
    tz_offset  = datetime.timedelta(seconds=data['city']['timezone'])
    now_local  = datetime.datetime.utcnow() + tz_offset
    today      = now_local.date()
    target     = today if day == 'today' else today + datetime.timedelta(days=1)

    slots = []
    for item in data['list']:
        dt_local = datetime.datetime.utcfromtimestamp(item['dt']) + tz_offset
        if dt_local.date() == target:
            slots.append((dt_local, item))

    if not slots:
        label = 'сегодня' if day == 'today' else 'завтра'
        return f'❌ Нет данных о погоде на {label}.'

    day_label  = 'сегодня' if day == 'today' else 'завтра'
    date_label = f'{target.day} {_MONTHS[target.month]}'
    lines = [f'🌍 <b>Погода в {city_name}</b> — {day_label}, {date_label}\n']

    temps, winds, humidities = [], [], []
    for dt_local, item in slots:
        temp  = round(item['main']['temp'])
        feels = round(item['main']['feels_like'])
        icon  = _icon(item['weather'][0]['icon'])
        desc  = item['weather'][0]['description'].capitalize()
        wind  = item['wind']['speed']
        hum   = item['main']['humidity']
        temps.append(temp); winds.append(wind); humidities.append(hum)
        lines.append(
            f'<code>{dt_local.strftime("%H:%M")}</code>  '
            f'<b>{temp:+d}°C</b> (ощущ. {feels:+d}°C)  {icon} {desc}'
        )

    lines.append(
        f'\n📊 Мин: <b>{min(temps):+d}°C</b>  |  Макс: <b>{max(temps):+d}°C</b>\n'
        f'💨 Ветер: до {max(winds):.0f} м/с  |  💧 Влажность: ~{round(sum(humidities)/len(humidities))}%'
    )
    return '\n'.join(lines)


# ──────────────── 5-day summary ────────────────

def _format_5days(data: dict) -> str:
    city_name = html.escape(data['city']['name'])
    tz_offset = datetime.timedelta(seconds=data['city']['timezone'])
    today     = (datetime.datetime.utcnow() + tz_offset).date()

    by_day = defaultdict(list)
    for item in data['list']:
        dt_local = datetime.datetime.utcfromtimestamp(item['dt']) + tz_offset
        by_day[dt_local.date()].append(item)

    lines = [f'🌍 <b>Прогноз на 5 дней — {city_name}</b>\n']

    for date_key in sorted(by_day.keys()):
        items  = by_day[date_key]
        temps  = [round(i['main']['temp']) for i in items]
        winds  = [i['wind']['speed'] for i in items]
        humids = [i['main']['humidity'] for i in items]
        icons  = [i['weather'][0]['icon'] for i in items]
        desc   = max(set(i['weather'][0]['description'] for i in items),
                     key=lambda d: sum(1 for i in items if i['weather'][0]['description'] == d))

        day_nm = _DAY_NAMES[date_key.weekday()]
        date_s = f'{date_key.day} {_MONTHS[date_key.month]}'
        main_icon = _icon(max(set(icons), key=icons.count))

        if date_key == today:
            suffix = ' (сегодня)'
        elif date_key == today + datetime.timedelta(days=1):
            suffix = ' (завтра)'
        else:
            suffix = ''

        lines.append(
            f'<b>{day_nm}, {date_s}{suffix}</b>\n'
            f'  {main_icon} {desc.capitalize()}\n'
            f'  🌡 {min(temps):+d}°C / {max(temps):+d}°C  '
            f'💨 {max(winds):.0f} м/с  💧 {round(sum(humids)/len(humids))}%'
        )

    return '\n\n'.join(lines)


# ──────────────── Public API ────────────────

def get_forecast(city: str, day: str) -> str:
    data = _fetch_forecast({'q': city})
    if data is None:
        return f'❌ Город "<b>{html.escape(city)}</b>" не найден.'
    return (_format_5days if day == 'week' else _format_day)(data, *(() if day == 'week' else (day,)))


def get_forecast_by_coords(lat: float, lon: float, day: str) -> str:
    data = _fetch_forecast({'lat': lat, 'lon': lon})
    if data is None:
        return '❌ Не удалось определить погоду по геолокации.'
    return (_format_5days if day == 'week' else _format_day)(data, *(() if day == 'week' else (day,)))
