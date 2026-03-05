from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_kb() -> ReplyKeyboardMarkup:
    """Главная клавиатура бота."""
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text='/news'),
            KeyboardButton(text='/weather'),
            KeyboardButton(text='/ai'),
        ]],
        resize_keyboard=True,
    )


def weather_kb() -> ReplyKeyboardMarkup:
    """Клавиатура для запроса погоды."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📍 Моё местоположение', request_location=True)],
            [KeyboardButton(text='❌ Отмена')],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
