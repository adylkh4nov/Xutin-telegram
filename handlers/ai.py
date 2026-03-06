import asyncio
import logging
import anthropic
from datetime import date
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from config import claude_token
from .utils import user_tag, short

router = Router()
log = logging.getLogger(__name__)

# Telegram ограничивает сообщение до 4096 символов
_TG_LIMIT = 4096

# Лимит запросов к Claude в сутки на одного пользователя
_DAILY_LIMIT = 5


class AIStates(StatesGroup):
    chatting = State()


def _build_history_pages(history: list) -> list[str]:
    """
    Формирует историю диалога в виде страниц,
    каждая не длиннее _TG_LIMIT символов.
    """
    pairs = []
    for i in range(0, len(history) - 1, 2):
        if history[i]['role'] == 'user' and history[i + 1]['role'] == 'assistant':
            pairs.append((history[i]['content'], history[i + 1]['content']))

    if not pairs:
        return []

    header = f'📋 <b>История диалога</b> ({len(pairs)} вопр.):\n'
    pages, current = [], header

    for idx, (question, answer) in enumerate(pairs, 1):
        block = (
            f'\n<b>#{idx} Вы:</b>\n'
            f'{question}\n\n'
            f'<b>🤖 Claude:</b>\n'
            f'{answer}\n'
            f'{"─" * 20}\n'
        )
        if len(current) + len(block) > _TG_LIMIT:
            pages.append(current)
            current = block
        else:
            current += block

    if current:
        pages.append(current)

    return pages


@router.message(Command('ai'), StateFilter('*'))
async def cmd_ai(message: Message, state: FSMContext):
    await state.set_state(AIStates.chatting)
    log.info('%s /ai → начал диалог с Claude', user_tag(message.from_user))
    await message.answer(
        '🤖 Введите запрос для Claude:\n\n'
        '<i>Claude помнит историю диалога.\n'
        '/history — посмотреть историю\n'
        '/clear — очистить историю</i>',
    )


@router.message(Command('history'), StateFilter('*'))
async def cmd_history(message: Message, state: FSMContext):
    log.info('%s /history', user_tag(message.from_user))
    data = await state.get_data()
    history: list = data.get('history', [])

    if not history:
        await message.answer('📋 История диалога пуста.\n\nНачните общение командой /ai')
        return

    pages = _build_history_pages(history)
    if not pages:
        await message.answer('📋 История диалога пуста.')
        return

    for page in pages:
        await message.answer(page)


@router.message(Command('clear'), StateFilter('*'))
async def cmd_clear(message: Message, state: FSMContext):
    await state.update_data(history=[])
    log.info('%s /clear — история очищена', user_tag(message.from_user))
    await message.answer('🗑 История диалога очищена.')


@router.message(AIStates.chatting, F.text)
async def ai_chat(message: Message, state: FSMContext):
    user = user_tag(message.from_user)
    log.info('%s /ai → "%s"', user, short(message.text))

    data = await state.get_data()

    # Проверка дневного лимита
    today_str  = date.today().isoformat()
    ai_date    = data.get('ai_date', '')
    ai_count   = data.get('ai_count', 0) if ai_date == today_str else 0

    if ai_count >= _DAILY_LIMIT:
        log.warning('%s /ai ← лимит исчерпан (%d/%d)', user, ai_count, _DAILY_LIMIT)
        await message.answer(
            f'⛔ Лимит {_DAILY_LIMIT} запросов в сутки исчерпан.\n'
            f'Возвращайтесь завтра!'
        )
        return

    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)

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
        ai_count += 1
        remaining = _DAILY_LIMIT - ai_count
        await state.update_data(history=history, ai_date=today_str, ai_count=ai_count)
        log.info('%s /ai ← "%s" (запросов сегодня: %d/%d)', user, short(reply), ai_count, _DAILY_LIMIT)
        suffix = f'\n\n<i>Осталось запросов сегодня: {remaining}</i>' if remaining <= 2 else ''
        await message.answer(reply + suffix)
    except Exception as e:
        log.error('%s /ai ← ОШИБКА: %s', user, e)
        await message.answer(f'❌ Ошибка Claude: {e}')
