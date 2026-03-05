"""Точка входа — запуск бота."""
import asyncio
import logging

from aiogram.types import BotCommand

from bot import bot, dp
from handlers import router


async def main():
    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command='news',    description='📰 Новости Tengri'),
        BotCommand(command='weather', description='🌤 Погода'),
        BotCommand(command='ai',      description='🤖 Спросить Claude'),
        BotCommand(command='history', description='📋 История диалога с Claude'),
        BotCommand(command='clear',   description='🗑 Очистить историю Claude'),
    ])

    logging.info('Бот запущен')
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8'),
        ],
    )
    asyncio.run(main())
