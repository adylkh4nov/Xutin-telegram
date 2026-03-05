import time
import logging
import bot  # регистрирует все хендлеры из answers.py
from bot_instance import bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
)

if __name__ == '__main__':
    logging.info('Бот запущен')
    while True:
        try:
            bot.polling(none_stop=True, timeout=30)
        except Exception as e:
            logging.error(f'Ошибка polling: {e}')
            logging.info('Перезапуск через 5 секунд...')
            time.sleep(5)
