import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from .keyboards import main_kb, weather_kb, weather_day_kb
from .utils import user_tag
from services import weather as weather_service

router = Router()
log = logging.getLogger(__name__)

_WEATHER_TIMEOUT = 12


class WeatherStates(StatesGroup):
    waiting     = State()   # ждёт город или геолокацию
    waiting_day = State()   # ждёт выбор дня (Сегодня / Завтра)


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


@router.message(F.location, StateFilter('*'))
async def weather_by_location(message: Message, state: FSMContext):
    lat, lon = message.location.latitude, message.location.longitude
    log.info('%s /weather coords=(%.4f, %.4f)', user_tag(message.from_user), lat, lon)
    await state.update_data(coords=(lat, lon), city=None)
    await state.set_state(WeatherStates.waiting_day)
    await message.answer('📅 Выберите день:', reply_markup=weather_day_kb())


@router.message(WeatherStates.waiting, F.text == '❌ Отмена')
async def weather_cancel(message: Message, state: FSMContext):
    await state.clear()
    log.info('%s /weather → отмена', user_tag(message.from_user))
    await message.answer('Отменено.', reply_markup=main_kb())


@router.message(WeatherStates.waiting, F.text)
async def weather_by_city(message: Message, state: FSMContext):
    city = message.text.strip()
    log.info('%s /weather city="%s"', user_tag(message.from_user), city)
    await state.update_data(city=city, coords=None)
    await state.set_state(WeatherStates.waiting_day)
    await message.answer('📅 Выберите день:', reply_markup=weather_day_kb())


@router.callback_query(
    F.data.in_({'weather:today', 'weather:tomorrow'}),
    StateFilter(WeatherStates.waiting_day),
)
async def weather_day_selected(callback: CallbackQuery, state: FSMContext):
    day  = 'today' if callback.data == 'weather:today' else 'tomorrow'
    data = await state.get_data()
    await state.clear()

    user = user_tag(callback.from_user)
    log.info('%s /weather → день: %s', user, day)

    await callback.answer()
    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    try:
        if data.get('coords'):
            lat, lon = data['coords']
            text = await asyncio.wait_for(
                asyncio.to_thread(weather_service.get_forecast_by_coords, lat, lon, day),
                timeout=_WEATHER_TIMEOUT,
            )
        else:
            city = data.get('city', '')
            text = await asyncio.wait_for(
                asyncio.to_thread(weather_service.get_forecast, city, day),
                timeout=_WEATHER_TIMEOUT,
            )
        log.info('%s /weather ← OK', user)
    except asyncio.TimeoutError:
        log.warning('%s /weather ← TIMEOUT', user)
        text = '❌ Сервис погоды не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('%s /weather ← ОШИБКА: %s', user, e)
        text = '❌ Не удалось получить прогноз погоды.'

    await callback.message.answer(text, reply_markup=main_kb())
