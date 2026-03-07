import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from .keyboards import main_kb, currency_choose_kb, currency_action_kb, currency_city_kb
from .utils import user_tag
from services import currency as currency_service

router = Router()
log = logging.getLogger(__name__)

_TIMEOUT = 20


class CurrencyStates(StatesGroup):
    waiting_location = State()   # ждёт геолокацию для ближайшего


# ──────────────── /currency ────────────────

@router.message(Command('currency'), StateFilter('*'))
async def cmd_currency(message: Message, state: FSMContext):
    data = await state.get_data()
    last_cur  = data.get('last_currency', '')
    last_city = data.get('last_currency_city', 'almaty')

    city_label = currency_service.CITIES.get(last_city, 'Алматы')
    log.info('%s /currency (last: %s %s)', user_tag(message.from_user), last_cur, last_city)

    await message.answer(
        '💱 Выберите валюту:',
        reply_markup=currency_choose_kb(last_cur, city_label if last_cur else ''),
    )


# ──────────────── Выбор валюты ────────────────

@router.callback_query(F.data.startswith('cur:'), StateFilter('*'))
async def currency_selected(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split(':')[1]   # USD / EUR / RUB / CNY / GBP

    data = await state.get_data()
    city_slug = data.get('last_currency_city', 'almaty')

    await callback.answer()
    await callback.message.edit_text(
        f'💱 Валюта: <b>{currency}</b> — загружаю курсы…',
        reply_markup=None,
    )

    await state.update_data(last_currency=currency)
    await _show_rates(callback.message, state, currency, city_slug)


# ──────────────── Сменить город ────────────────

@router.callback_query(F.data == 'cur_city', StateFilter('*'))
async def currency_change_city(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cur  = data.get('last_currency', 'USD')

    await callback.answer()
    await callback.message.edit_text(
        f'🏙 Выберите город для курса <b>{cur}</b>:',
        reply_markup=currency_city_kb(),
    )


@router.callback_query(F.data.startswith('cur_city:'), StateFilter('*'))
async def currency_city_selected(callback: CallbackQuery, state: FSMContext):
    city_slug = callback.data.split(':')[1]

    data = await state.get_data()
    currency = data.get('last_currency', 'USD')

    await callback.answer()
    await callback.message.edit_text(
        f'💱 {currency} — {currency_service.CITIES.get(city_slug, city_slug)}…',
        reply_markup=None,
    )

    await state.update_data(last_currency_city=city_slug)
    await _show_rates(callback.message, state, currency, city_slug)


# ──────────────── Ближайший по геолокации ────────────────

@router.callback_query(F.data == 'cur_near', StateFilter('*'))
async def currency_nearest_prompt(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cur  = data.get('last_currency', 'USD')

    await callback.answer()
    await callback.message.answer(
        f'📍 Отправьте геолокацию — найду ближайшие обменники для <b>{cur}</b>:',
        reply_markup=_location_kb(),
    )
    await state.set_state(CurrencyStates.waiting_location)


@router.message(CurrencyStates.waiting_location, F.location)
async def currency_by_location(message: Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude

    data = await state.get_data()
    currency = data.get('last_currency', 'USD')

    log.info('%s /currency nearest coords=(%.4f, %.4f) %s',
             user_tag(message.from_user), lat, lon, currency)

    await state.set_state(None)
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(currency_service.get_nearest, lat, lon, currency),
            timeout=_TIMEOUT,
        )
    except asyncio.TimeoutError:
        text = '❌ Сервис не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('%s /currency nearest ← ОШИБКА: %s', user_tag(message.from_user), e)
        text = '❌ Не удалось получить данные.'

    await message.answer(text, reply_markup=main_kb())


@router.message(CurrencyStates.waiting_location, F.text == '❌ Отмена')
async def currency_location_cancel(message: Message, state: FSMContext):
    await state.set_state(None)
    await message.answer('Отменено.', reply_markup=main_kb())


# ──────────────── Сменить валюту (из результатов) ────────────────

@router.callback_query(F.data == 'cur_switch', StateFilter('*'))
async def currency_switch(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    last_cur = data.get('last_currency', '')

    await callback.answer()
    await callback.message.edit_text('💱 Выберите валюту:', reply_markup=None)
    await callback.message.answer(
        '💱 Выберите валюту:',
        reply_markup=currency_choose_kb(last_cur),
    )


# ──────────────── Повторить последний запрос ────────────────

@router.callback_query(F.data == 'cur_repeat', StateFilter('*'))
async def currency_repeat(callback: CallbackQuery, state: FSMContext):
    data      = await state.get_data()
    currency  = data.get('last_currency', 'USD')
    city_slug = data.get('last_currency_city', 'almaty')

    await callback.answer()
    await callback.message.edit_text(
        f'💱 {currency} — {currency_service.CITIES.get(city_slug, city_slug)}…',
        reply_markup=None,
    )
    await _show_rates(callback.message, state, currency, city_slug)


# ──────────────── Helpers ────────────────

async def _show_rates(message: Message, state: FSMContext, currency: str, city_slug: str):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        text = await asyncio.wait_for(
            asyncio.to_thread(currency_service.get_rates, currency, city_slug),
            timeout=_TIMEOUT,
        )
    except asyncio.TimeoutError:
        text = '❌ Сервис не ответил вовремя. Попробуйте позже.'
    except Exception as e:
        log.error('/currency get_rates ← ОШИБКА: %s', e)
        text = '❌ Не удалось получить курсы.'

    await message.answer(text, reply_markup=currency_action_kb(currency))


def _location_kb():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📍 Моё местоположение', request_location=True)],
            [KeyboardButton(text='❌ Отмена')],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
