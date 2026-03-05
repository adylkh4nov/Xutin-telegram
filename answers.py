import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

import tenrgi
import weather as w
from config import claude_token
import anthropic

router = Router()
log = logging.getLogger(__name__)


# ─── FSM состояния ───────────────────────────────────────────────────────────

class WeatherStates(StatesGroup):
    waiting = State()

class AIStates(StatesGroup):
    chatting = State()


# ─── Клавиатуры ──────────────────────────────────────────────────────────────

def _main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='/start'),   KeyboardButton(text='/news')],
            [KeyboardButton(text='/weather'), KeyboardButton(text='/AI')],
        ],
        resize_keyboard=True,
    )

def _weather_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📍 Моё местоположение', request_location=True)],
            [KeyboardButton(text='❌ Отмена')],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


# ─── /start ──────────────────────────────────────────────────────────────────

@router.message(Command('start'), StateFilter('*'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f'Привет, {message.from_user.first_name}! 👋\n\nВыбери команду:',
        reply_markup=_main_kb(),
    )


# ─── /news ───────────────────────────────────────────────────────────────────

@router.message(Command('news'), StateFilter('*'))
async def cmd_news(message: Message):
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='🔗 Открыть сайт', url='https://tengrinews.kz/'),
    ]])
    try:
        # requests — синхронный, запускаем в потоке чтобы не блокировать event loop
        text = await asyncio.to_thread(tenrgi.get_news)
    except Exception as e:
        log.error('tenrgi error: %s', e)
        text = '❌ Не удалось загрузить новости.'
    await message.answer(text, reply_markup=markup, disable_web_page_preview=True)


# ─── /weather ────────────────────────────────────────────────────────────────

@router.message(Command('weather'), StateFilter('*'))
async def cmd_weather(message: Message, state: FSMContext):
    await state.set_state(WeatherStates.waiting)
    await message.answer(
        '🏙 Введите название города или отправьте геолокацию:',
        reply_markup=_weather_kb(),
    )

# Геолокация работает в ЛЮБОМ состоянии — кнопка может остаться на экране
@router.message(F.location, StateFilter('*'))
async def weather_by_location(message: Message, state: FSMContext):
    await state.clear()
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    try:
        text = await asyncio.to_thread(
            w.get_weather_by_coords,
            message.location.latitude,
            message.location.longitude,
        )
    except Exception as e:
        log.error('weather_by_coords error: %s', e)
        text = '❌ Не удалось получить погоду по геолокации.'
    await message.answer(text, reply_markup=_main_kb())

@router.message(WeatherStates.waiting, F.text == '❌ Отмена')
async def weather_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Отменено.', reply_markup=_main_kb())

@router.message(WeatherStates.waiting, F.text)
async def weather_by_city(message: Message, state: FSMContext):
    await state.clear()
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    try:
        text = await asyncio.to_thread(w.get_weather, message.text.strip())
    except Exception as e:
        log.error('weather_by_city error: %s', e)
        text = '❌ Не удалось получить погоду.'
    await message.answer(text, reply_markup=_main_kb())


# ─── /AI ─────────────────────────────────────────────────────────────────────

@router.message(Command('AI'), StateFilter('*'))
async def cmd_ai(message: Message, state: FSMContext):
    await state.set_state(AIStates.chatting)
    await message.answer(
        '🤖 Введите запрос для Claude:\n\n'
        '<i>Claude помнит историю диалога. /clear — очистить историю.</i>',
    )

@router.message(Command('clear'), StateFilter('*'))
async def cmd_clear(message: Message, state: FSMContext):
    await state.update_data(history=[])
    await message.answer('🗑 История диалога очищена.')

@router.message(AIStates.chatting, F.text)
async def ai_chat(message: Message, state: FSMContext):
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)

    data = await state.get_data()
    history: list = data.get('history', [])
    history.append({'role': 'user', 'content': message.text})

    if len(history) > 20:
        history = history[-20:]

    try:
        # Anthropic SDK тоже синхронный — запускаем в потоке
        def _call_claude():
            client = anthropic.Anthropic(api_key=claude_token)
            return client.messages.create(
                model='claude-opus-4-6',
                max_tokens=2000,
                messages=history,
            )

        response = await asyncio.to_thread(_call_claude)
        reply = response.content[0].text
        history.append({'role': 'assistant', 'content': reply})
        await state.update_data(history=history)
        await message.answer(reply)
    except Exception as e:
        log.error('claude error: %s', e)
        await message.answer(f'❌ Ошибка Claude: {e}')


# ─── Catch-all — любое необработанное сообщение ──────────────────────────────

@router.message(StateFilter('*'))
async def fallback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        'Выбери команду 👇',
        reply_markup=_main_kb(),
    )
