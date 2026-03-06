"""Курсы валют через API kurs.kz (paladin.kurs.finance)."""
import html
import math
import warnings
import datetime
import requests

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

_API      = 'https://paladin.kurs.finance/punkts/'
_HEADERS  = {'User-Agent': 'Mozilla/5.0 (compatible; TelegramBot)'}

# Точные названия городов из API
CITIES = {
    'almaty':    'Алматы',
    'astana':    'Нур-Султан',
    'shymkent':  'Шымкент',
    'pavlodar':  'Павлодар',
    'kostanay':  'Костанай',
}

CURRENCIES = ['USD', 'EUR', 'RUB', 'CNY', 'GBP']

_CURRENCY_FLAG = {
    'USD': '🇺🇸', 'EUR': '🇪🇺', 'RUB': '🇷🇺',
    'CNY': '🇨🇳', 'GBP': '🇬🇧',
}


def _fetch() -> list[dict]:
    r = requests.get(_API, headers=_HEADERS, verify=False, timeout=15)
    r.encoding = 'utf-8'
    return r.json()


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние в км между двумя точками."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _work_status(p: dict) -> str:
    wa = p.get('workattr', {})
    if wa.get('nonstop'):
        return '🟢 Круглосуточно'
    if wa.get('closed'):
        return '🔴 Закрыто'
    if wa.get('worknow'):
        wm = p.get('workmodes', {})
        day_key = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'][datetime.datetime.now().weekday()]
        hours = wm.get(day_key, ['', ''])
        return f'🟢 {hours[0]}–{hours[1]}' if hours[0] else '🟢 Открыто'
    return '🔴 Закрыто'


def _filter_by_city(data: list, city_slug: str) -> list:
    city_name = CITIES.get(city_slug, '')
    return [p for p in data if p.get('city', '') == city_name]


def _valid_punkts(data: list, currency: str) -> list:
    """Только актуальные обменники с ненулевым курсом."""
    result = []
    for p in data:
        if p.get('workattr', {}).get('closed'):
            continue
        rates = p.get('data', {}).get(currency, [0, 0])
        if rates[0] > 0 and rates[1] > 0:
            result.append(p)
    return result


def get_rates(currency: str, city_slug: str = 'almaty') -> str:
    """Топ обменников по курсу покупки в городе."""
    try:
        all_data = _fetch()
    except Exception as e:
        return f'❌ Ошибка подключения к kurs.kz: {html.escape(str(e))}'

    city_data  = _filter_by_city(all_data, city_slug)
    punkts     = _valid_punkts(city_data, currency)

    if not punkts:
        return f'❌ Нет данных по {currency} для города {CITIES.get(city_slug, city_slug)}.'

    # Сортируем по покупке (выше = лучше для клиента)
    punkts.sort(key=lambda p: p['data'][currency][0], reverse=True)
    top = punkts[:10]

    flag = _CURRENCY_FLAG.get(currency, '💱')
    city_label = CITIES.get(city_slug, city_slug)
    now_str = datetime.datetime.now().strftime('%H:%M')

    lines = [
        f'{flag} <b>Курс {currency}/KZT — {city_label}</b>',
        f'<i>Обновлено: {now_str}</i>\n',
    ]

    for i, p in enumerate(top, 1):
        rates   = p['data'][currency]
        buy, sell = rates[0], rates[1]
        name    = html.escape(p.get('name', '—'))
        addr    = html.escape(p.get('mainaddress') or p.get('address') or '—')
        status  = _work_status(p)

        lines.append(
            f'<b>{i}. {name}</b>  {status}\n'
            f'   🛒 Покупка: <b>{buy:.2f}</b>  |  💰 Продажа: <b>{sell:.2f}</b>\n'
            f'   📍 {addr}'
        )

    return '\n\n'.join(lines)


def get_nearest(lat: float, lon: float, currency: str, radius_km: float = 10.0) -> str:
    """Ближайшие обменники по координатам."""
    try:
        all_data = _fetch()
    except Exception as e:
        return f'❌ Ошибка подключения к kurs.kz: {html.escape(str(e))}'

    punkts = _valid_punkts(all_data, currency)

    nearby = []
    for p in punkts:
        try:
            p_lat = float(p.get('lat') or 0)
            p_lon = float(p.get('lng') or 0)
        except (TypeError, ValueError):
            continue
        if p_lat == 0 or p_lon == 0:
            continue

        dist = _haversine(lat, lon, p_lat, p_lon)
        if dist <= radius_km:
            nearby.append((dist, p))

    if not nearby:
        return (f'❌ Обменников с курсом {currency} в радиусе {radius_km:.0f} км не найдено.\n'
                f'Попробуйте выбрать город вручную.')

    nearby.sort(key=lambda x: x[0])
    top = nearby[:5]

    flag = _CURRENCY_FLAG.get(currency, '💱')
    lines = [f'{flag} <b>Ближайшие обменники ({currency}/KZT)</b>\n']

    for dist, p in top:
        rates     = p['data'][currency]
        buy, sell = rates[0], rates[1]
        name      = html.escape(p.get('name', '—'))
        addr      = html.escape(p.get('mainaddress') or p.get('address') or '—')
        status    = _work_status(p)

        dist_str = f'{dist * 1000:.0f} м' if dist < 1 else f'{dist:.1f} км'

        lines.append(
            f'<b>{name}</b>  {status}\n'
            f'   🛒 Покупка: <b>{buy:.2f}</b>  |  💰 Продажа: <b>{sell:.2f}</b>\n'
            f'   📍 {addr}\n'
            f'   🚶 {dist_str}'
        )

    return '\n\n'.join(lines)
