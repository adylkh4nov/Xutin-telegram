import asyncio
import logging

from aiogram.types import BotCommand
from bot_instance import bot, dp
import answers  # регистрирует router с хендлерами


async def main():
    dp.include_router(answers.router)

    # Команды в меню Telegram (кнопка "/" у поля ввода)
    await bot.set_my_commands([
        BotCommand(command='news',    description='📰 Новости Tengri'),
        BotCommand(command='weather', description='🌤 Погода'),
        BotCommand(command='AI',      description='🤖 Спросить Claude'),
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
            logging.StreamHandler(),                        # консоль
            logging.FileHandler('bot.log', encoding='utf-8'),  # файл
        ],
    )
    asyncio.run(main())
