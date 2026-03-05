import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from .keyboards import main_kb, weather_kb
from .utils import user_tag
from services import weather as weather_service

router = Router()
log = logging.getLogger(__name__)

# Таймаут на запрос к OpenWeatherMap (секунды)
_WEATHER_TIMEOUT = 12


class WeatherStates(StatesGroup):
    waiting = State()


@router.message(Command('weather'), StateFilter('*'))
async def cmd_weather(message: Message, state: FSMContext):
    await state.set_state(WeatherStates.waiting)
    log.info('%s /weather → ожидает город или геолокацию', user_tag(message.from_user))
    await message.answer(
        '🏙 Введите название города или отправьте геолокацию:\n\n'
        '<i>Если геолокация недоступна — проверьте разрешения:\n'
        'Настройки → Telegram → Геопозиция → При использовании</i>',
        reply_markup=weather_kb(),
    )


# Геолокация — в любом состоянии (кнопка может оставаться на экране)
@router.message(F.location, StateFilter('*'))
async def weather_by_location(message: Message, state: FSMContext):
    await state.clear()
    lat, lon = message.location.latitude, message.location.longitude
    log.info('%s /weather coords=(%.4f, %.4f)', user_tag(message.from_user), lat, lon)
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(weather_service.get_weather_by_coords, lat, lon),
            timeout=_WEATHER_TIMEOUT,
        )
        log.info('%s /weather coords ← OK', user_tag(message.from_user))
    except asyncio.TimeoutError:
        log.warning('%s /weather coords ← TIMEOUT', user_tag(message.from_user))
        text = '❌ Сервис погоды не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('%s /weather coords ← ОШИБКА: %s', user_tag(message.from_user), e)
        text = '❌ Не удалось получить погоду по геолокации.'
    await message.answer(text, reply_markup=main_kb())


@router.message(WeatherStates.waiting, F.text == '❌ Отмена')
async def weather_cancel(message: Message, state: FSMContext):
    await state.clear()
    log.info('%s /weather → отмена', user_tag(message.from_user))
    await message.answer('Отменено.', reply_markup=main_kb())


@router.message(WeatherStates.waiting, F.text)
async def weather_by_city(message: Message, state: FSMContext):
    city = message.text.strip()
    await state.clear()
    log.info('%s /weather city="%s"', user_tag(message.from_user), city)
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(weather_service.get_weather, city),
            timeout=_WEATHER_TIMEOUT,
        )
        log.info('%s /weather city ← OK', user_tag(message.from_user))
    except asyncio.TimeoutError:
        log.warning('%s /weather city ← TIMEOUT', user_tag(message.from_user))
        text = '❌ Сервис погоды не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('%s /weather city ← ОШИБКА: %s', user_tag(message.from_user), e)
        text = '❌ Не удалось получить погоду.'
    await message.answer(text, reply_markup=main_kb())
