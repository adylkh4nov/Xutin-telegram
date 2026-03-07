from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)


# ──────────────── Reply keyboards ────────────────

def main_kb() -> ReplyKeyboardMarkup:
    """Главная клавиатура бота."""
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text='/news'),
            KeyboardButton(text='/weather'),
            KeyboardButton(text='/currency'),
            KeyboardButton(text='/ai'),
        ]],
        resize_keyboard=True,
    )


def weather_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса погоды (без сохранённого города)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📍 Моё местоположение', request_location=True)],
            [KeyboardButton(text='❌ Отмена')],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def weather_city_kb(city: str = '', has_last_coords: bool = False) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопками последнего города и/или геолокации."""
    kb = []
    if city:
        kb.append([KeyboardButton(text=f'🏙 {city}')])
    if has_last_coords:
        kb.append([KeyboardButton(text='📍 Последнее место')])
    kb.append([KeyboardButton(text='📍 Моё местоположение', request_location=True)])
    kb.append([KeyboardButton(text='❌ Отмена')])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


# ──────────────── Weather inline ────────────────

def weather_day_kb() -> InlineKeyboardMarkup:
    """Выбор периода прогноза."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='📅 Сегодня',  callback_data='weather:today'),
        InlineKeyboardButton(text='📅 Завтра',   callback_data='weather:tomorrow'),
        InlineKeyboardButton(text='📆 5 дней',   callback_data='weather:week'),
    ]])


# ──────────────── Currency inline ────────────────

def currency_choose_kb(last_currency: str = '', last_city_label: str = '') -> InlineKeyboardMarkup:
    """Выбор валюты."""
    currencies = [
        ('🇺🇸 USD', 'cur:USD'),
        ('🇪🇺 EUR', 'cur:EUR'),
        ('🇷🇺 RUB', 'cur:RUB'),
        ('🇨🇳 CNY', 'cur:CNY'),
        ('🇬🇧 GBP', 'cur:GBP'),
    ]
    buttons = [
        InlineKeyboardButton(
            text=f'✅ {label}' if f'cur:{last_currency}' == cb else label,
            callback_data=cb,
        )
        for label, cb in currencies
    ]
    rows = [buttons[:3], buttons[3:]]
    if last_currency and last_city_label:
        rows.append([InlineKeyboardButton(
            text=f'🔄 Повторить: {last_currency} · {last_city_label}',
            callback_data='cur_repeat',
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def currency_action_kb(currency: str) -> InlineKeyboardMarkup:
    """Кнопки под результатами курса."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📍 Ближайший', callback_data='cur_near'),
            InlineKeyboardButton(text='🏙 Город',     callback_data='cur_city'),
        ],
        [
            InlineKeyboardButton(text='🔄 Другая валюта', callback_data=f'cur_switch'),
        ],
    ])


def currency_city_kb() -> InlineKeyboardMarkup:
    """Выбор города для курса валют."""
    cities = [
        ('Алматы',    'cur_city:almaty'),
        ('Астана',    'cur_city:astana'),
        ('Шымкент',   'cur_city:shymkent'),
        ('Павлодар',  'cur_city:pavlodar'),
        ('Костанай',  'cur_city:kostanay'),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=cb)]
        for label, cb in cities
    ])
