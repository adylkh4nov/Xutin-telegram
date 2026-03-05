import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from .keyboards import main_kb, weather_kb
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
    # send_chat_action — мгновенно показывает «печатает…», не требует редактирования
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(
                weather_service.get_weather_by_coords,
                message.location.latitude,
                message.location.longitude,
            ),
            timeout=_WEATHER_TIMEOUT,
        )
    except asyncio.TimeoutError:
        log.warning('weather coords timeout')
        text = '❌ Сервис погоды не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('weather coords error: %s', e)
        text = '❌ Не удалось получить погоду по геолокации.'
    await message.answer(text, reply_markup=main_kb())


@router.message(WeatherStates.waiting, F.text == '❌ Отмена')
async def weather_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Отменено.', reply_markup=main_kb())


@router.message(WeatherStates.waiting, F.text)
async def weather_by_city(message: Message, state: FSMContext):
    await state.clear()
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(weather_service.get_weather, message.text.strip()),
            timeout=_WEATHER_TIMEOUT,
        )
    except asyncio.TimeoutError:
        log.warning('weather city timeout')
        text = '❌ Сервис погоды не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('weather city error: %s', e)
        text = '❌ Не удалось получить погоду.'
    await message.answer(text, reply_markup=main_kb())
