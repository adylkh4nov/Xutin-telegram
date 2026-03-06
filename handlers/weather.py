import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from .keyboards import main_kb, weather_kb, weather_city_kb, weather_day_kb
from .utils import user_tag
from services import weather as weather_service

router = Router()
log = logging.getLogger(__name__)

_WEATHER_TIMEOUT = 12

_DAY_LABELS = {
    'today':    'Сегодня',
    'tomorrow': 'Завтра',
    'week':     '5 дней',
}


class WeatherStates(StatesGroup):
    waiting     = State()   # ждёт город или геолокацию
    waiting_day = State()   # ждёт выбор дня


# ──────────────── /weather ────────────────

@router.message(Command('weather'), StateFilter('*'))
async def cmd_weather(message: Message, state: FSMContext):
    data = await state.get_data()
    last_city = data.get('last_city')

    await state.set_state(WeatherStates.waiting)
    log.info('%s /weather → ожидает город', user_tag(message.from_user))

    if last_city:
        await message.answer(
            f'🏙 Последний город: <b>{last_city}</b>\n\n'
            f'Нажмите кнопку или введите другой:',
            reply_markup=weather_city_kb(last_city),
        )
    else:
        await message.answer(
            '🏙 Введите название города или отправьте геолокацию:\n\n'
            '<i>Если геолокация недоступна — проверьте разрешения:\n'
            'Настройки → Telegram → Геопозиция → При использовании</i>',
            reply_markup=weather_kb(),
        )


# ──────────────── Геолокация ────────────────

@router.message(F.location, StateFilter('*'))
async def weather_by_location(message: Message, state: FSMContext):
    lat, lon = message.location.latitude, message.location.longitude
    log.info('%s /weather coords=(%.4f, %.4f)', user_tag(message.from_user), lat, lon)
    await state.update_data(coords=(lat, lon), city=None)
    await state.set_state(WeatherStates.waiting_day)
    await message.answer('📅 Выберите период:', reply_markup=weather_day_kb())


# ──────────────── Отмена / ввод города ────────────────

@router.message(WeatherStates.waiting, F.text == '❌ Отмена')
async def weather_cancel(message: Message, state: FSMContext):
    await state.set_state(None)
    log.info('%s /weather → отмена', user_tag(message.from_user))
    await message.answer('Отменено.', reply_markup=main_kb())


@router.message(WeatherStates.waiting, F.text)
async def weather_by_city(message: Message, state: FSMContext):
    city = message.text.strip()
    # Убираем эмодзи-префикс сохранённого города (🏙 Алматы → Алматы)
    if city.startswith('🏙 '):
        city = city[2:].strip()

    log.info('%s /weather city="%s"', user_tag(message.from_user), city)
    await state.update_data(city=city, coords=None)
    await state.set_state(WeatherStates.waiting_day)
    await message.answer('📅 Выберите период:', reply_markup=weather_day_kb())


# ──────────────── Выбор дня (inline callback) ────────────────

@router.callback_query(
    F.data.in_({'weather:today', 'weather:tomorrow', 'weather:week'}),
    StateFilter(WeatherStates.waiting_day),
)
async def weather_day_selected(callback: CallbackQuery, state: FSMContext):
    day  = callback.data.split(':')[1]    # today / tomorrow / week
    data = await state.get_data()

    label = _DAY_LABELS[day]
    await callback.answer()
    # Убираем кнопки с сообщения — предотвращает повторные нажатия
    await callback.message.edit_text(f'📅 Выбрано: {label}', reply_markup=None)

    user = user_tag(callback.from_user)
    log.info('%s /weather → период: %s', user, day)

    await callback.message.bot.send_chat_action(callback.message.chat.id, ChatAction.TYPING)

    try:
        if data.get('coords'):
            lat, lon = data['coords']
            text = await asyncio.wait_for(
                asyncio.to_thread(weather_service.get_forecast_by_coords, lat, lon, day),
                timeout=_WEATHER_TIMEOUT,
            )
            # Для геолокации город не запоминаем
        else:
            city = data.get('city', '')
            text = await asyncio.wait_for(
                asyncio.to_thread(weather_service.get_forecast, city, day),
                timeout=_WEATHER_TIMEOUT,
            )
            # Сохраняем город если прогноз получен успешно
            if not text.startswith('❌'):
                await state.update_data(last_city=city)

        log.info('%s /weather ← OK', user)
    except asyncio.TimeoutError:
        log.warning('%s /weather ← TIMEOUT', user)
        text = '❌ Сервис погоды не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('%s /weather ← ОШИБКА: %s', user, e)
        text = '❌ Не удалось получить прогноз погоды.'
    finally:
        await state.set_state(None)

    await callback.message.answer(text, reply_markup=main_kb())
