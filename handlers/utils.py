"""Вспомогательные утилиты для хендлеров."""
from aiogram.types import User


def user_tag(user: User) -> str:
    """Возвращает строку вида: [123456789 | @username | Имя]"""
    uid = user.id
    username = f'@{user.username}' if user.username else 'no_username'
    name = user.full_name or '—'
    return f'[{uid} | {username} | {name}]'


def short(text: str, limit: int = 80) -> str:
    """Обрезает длинный текст для лога."""
    text = text.replace('\n', ' ')
    return text if len(text) <= limit else text[:limit] + '…'
