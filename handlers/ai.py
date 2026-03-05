import asyncio
import logging
import anthropic
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from config import claude_token

router = Router()
log = logging.getLogger(__name__)


class AIStates(StatesGroup):
    chatting = State()


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
