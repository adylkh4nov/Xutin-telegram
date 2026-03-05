import asyncio
import logging
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatAction

from services import news as news_service
from .utils import user_tag

router = Router()
log = logging.getLogger(__name__)


@router.message(Command('news'), StateFilter('*'))
async def cmd_news(message: Message):
    log.info('%s /news → запрос новостей', user_tag(message.from_user))
    await message.bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='🔗 Открыть сайт', url='https://tengrinews.kz/'),
    ]])
    try:
        text = await asyncio.to_thread(news_service.get_news)
        log.info('%s /news ← получены новости (%d симв.)', user_tag(message.from_user), len(text))
    except Exception as e:
        log.error('%s /news ← ОШИБКА: %s', user_tag(message.from_user), e)
        text = '❌ Не удалось загрузить новости.'
    await message.answer(text, reply_markup=markup, disable_web_page_preview=True)
