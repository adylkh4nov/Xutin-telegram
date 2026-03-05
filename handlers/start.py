import logging
from aiogram import Router
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from .keyboards import main_kb

router = Router()
log = logging.getLogger(__name__)


@router.message(Command('start'), StateFilter('*'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f'Привет, {message.from_user.first_name}! 👋\n\nВыбери команду:',
        reply_markup=main_kb(),
    )


# Catch-all — любое необработанное сообщение (регистрировать последним!)
@router.message(StateFilter('*'))
async def fallback(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Выбери команду 👇', reply_markup=main_kb())
