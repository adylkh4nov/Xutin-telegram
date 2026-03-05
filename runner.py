import asyncio
import logging

from bot_instance import bot, dp
import answers  # регистрирует router с хендлерами


async def main():
    dp.include_router(answers.router)
    logging.info('Бот запущен')
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S',
    )
    asyncio.run(main())
