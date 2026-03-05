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
    markup.add(types.InlineKeyboardButton('🔗 Источник', url='https://tengrinews.kz/'))
    text = tenrgi.get_news()
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode='Markdown')


# ─────────────────────────────── /weather ───────────────────────────────

@bot.message_handler(commands=['weather'])
def weather(message):
    mesg = bot.reply_to(message, '🏙 Введите название города:')
    bot.register_next_step_handler(mesg, _get_weather)


def _get_weather(message):
    bot.send_chat_action(message.chat.id, 'typing')
    text = w.get_weather(message.text)
    bot.send_message(message.chat.id, text, parse_mode='Markdown')


# ──────────────────────────────── /AI ───────────────────────────────────

@bot.message_handler(commands=['AI'])
def ai_start(message):
    mesg = bot.reply_to(message, '🤖 Введите запрос для Claude:\n\n_Напишите /clear чтобы очистить историю диалога_', parse_mode='Markdown')
    bot.register_next_step_handler(mesg, _get_claude_response)


@bot.message_handler(commands=['clear'])
def clear_history(message):
    _chat_history.pop(message.chat.id, None)
    bot.send_message(message.chat.id, '🗑 История диалога очищена.')


def _get_claude_response(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    # Добавляем сообщение пользователя в историю
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

        # Сохраняем ответ Claude в историю
        history.append({'role': 'assistant', 'content': reply})

        bot.send_message(chat_id, reply)
    except Exception as e:
        bot.send_message(chat_id, f'Ошибка Claude: {e}')
