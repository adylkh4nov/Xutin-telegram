"""Парсинг новостей с tengrinews.kz."""
import html
import warnings
import requests
from bs4 import BeautifulSoup as bs

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

BASE_URL = 'https://tengrinews.kz'
URL_TENGRI = f'{BASE_URL}/'


def _abs(href: str) -> str:
    """Превращает относительный URL в абсолютный."""
    return href if href.startswith('http') else BASE_URL + href


def _parse(url: str) -> list[tuple[str, str]]:
    """Возвращает список (заголовок, ссылка)."""
    r = requests.get(url, verify=False, timeout=10)
    r.encoding = 'utf-8'
    soup = bs(r.text, 'html.parser')

    results = []
    for cls in ('main-news_super_item_title', 'main-news_top_item_data'):
        for div in soup.find_all('div', class_=cls):
            a = div.find_parent('a') or div.find('a')
            title = div.get_text(strip=True)
            link = _abs(a['href']) if a else URL_TENGRI
            if title:
                results.append((title, link))
    return results


def get_news() -> str:
    """Возвращает HTML-строку со ссылками для Telegram."""
    items = _parse(URL_TENGRI)
    if not items:
        return 'Новости не найдены'

    lines = ['<b>📰 Новости Tengri News:</b>\n']
    for i, (title, link) in enumerate(items[:7], 1):
        lines.append(f'{i}. <a href="{link}">{html.escape(title)}</a>')
    return '\n'.join(lines)
