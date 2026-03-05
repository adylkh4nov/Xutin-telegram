import logging
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from .keyboards import main_kb
from .utils import user_tag, short

router = Router()
log = logging.getLogger(__name__)


@router.message(Command('start'), StateFilter('*'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    log.info('%s /start', user_tag(message.from_user))
    await message.answer(
        f'Привет, {message.from_user.first_name}! 👋\n\nВыбери команду:',
        reply_markup=main_kb(),
    )


# Catch-all — любое необработанное сообщение (регистрировать последним!)
@router.message(StateFilter('*'))
async def fallback(message: Message, state: FSMContext):
    await state.clear()
    log.info('%s fallback: "%s"', user_tag(message.from_user), short(message.text or '<не текст>'))
    await message.answer('Выбери команду 👇', reply_markup=main_kb())
