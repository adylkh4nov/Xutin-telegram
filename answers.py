from bot_instance import bot
from telebot import types
import tenrgi
import weather as w
from config import claude_token
import anthropic

# История диалогов с Claude: {chat_id: [{"role": ..., "content": ...}]}
_chat_history: dict = {}


def _get_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton('/start'),
        types.KeyboardButton('/news'),
        types.KeyboardButton('/weather'),
        types.KeyboardButton('/AI'),
    )
    return markup


# ──────────────────────────────── /start ────────────────────────────────

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        f'Привет, {message.from_user.first_name}! 👋\n\nВыбери команду:',
        reply_markup=_get_markup(),
    )


# ──────────────────────────────── /news ─────────────────────────────────

@bot.message_handler(commands=['news'])
def news(message):
    bot.send_chat_action(message.chat.id, 'typing')
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🔗 Открыть сайт', url='https://tengrinews.kz/'))
    text = tenrgi.get_news()
    bot.send_message(
        message.chat.id, text,
        reply_markup=markup,
        parse_mode='HTML',
        disable_web_page_preview=True,
    )


# ─────────────────────────────── /weather ───────────────────────────────

@bot.message_handler(commands=['weather'])
def weather(message):
    # Кнопка геолокации + отмена
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('📍 Моё местоположение', request_location=True))
    markup.add(types.KeyboardButton('❌ Отмена'))
    mesg = bot.send_message(
        message.chat.id,
        '🏙 Введите название города или отправьте геолокацию:',
        reply_markup=markup,
    )
    bot.register_next_step_handler(mesg, _handle_weather_input)


def _handle_weather_input(message):
    # Отмена
    if message.text and message.text.strip() == '❌ Отмена':
        bot.send_message(message.chat.id, 'Отменено.', reply_markup=_get_markup())
        return

    bot.send_chat_action(message.chat.id, 'typing')

    if message.location:
        text = w.get_weather_by_coords(
            message.location.latitude,
            message.location.longitude,
        )
    else:
        text = w.get_weather(message.text.strip())

    bot.send_message(message.chat.id, text, parse_mode='HTML', reply_markup=_get_markup())


# ──────────────────────────────── /AI ───────────────────────────────────

@bot.message_handler(commands=['AI'])
def ai_start(message):
    mesg = bot.reply_to(
        message,
        '🤖 Введите запрос для Claude:\n\n'
        '<i>Напишите /clear чтобы очистить историю диалога</i>',
        parse_mode='HTML',
    )
    bot.register_next_step_handler(mesg, _get_claude_response)


@bot.message_handler(commands=['clear'])
def clear_history(message):
    _chat_history.pop(message.chat.id, None)
    bot.send_message(message.chat.id, '🗑 История диалога очищена.')


def _get_claude_response(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    history = _chat_history.setdefault(chat_id, [])
    history.append({'role': 'user', 'content': message.text})

    # Ограничиваем историю последними 20 сообщениями (10 пар)
    if len(history) > 20:
        history = history[-20:]
        _chat_history[chat_id] = history

    try:
        client = anthropic.Anthropic(api_key=claude_token)
        response = client.messages.create(
            model='claude-opus-4-6',
            max_tokens=2000,
            messages=history,
        )
        reply = response.content[0].text
        history.append({'role': 'assistant', 'content': reply})
        bot.send_message(chat_id, reply)
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка Claude: {e}')
