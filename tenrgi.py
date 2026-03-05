import html
import warnings
import requests
from bs4 import BeautifulSoup as bs

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

BASE_URL = 'https://tengrinews.kz'
URL_TENGRI = f'{BASE_URL}/'


def _abs(href: str) -> str:
    """Превращает относительный URL в абсолютный."""
    if href.startswith('http'):
        return href
    return BASE_URL + href


def parse_tengri(url: str) -> list[tuple[str, str]]:
    """Возвращает список (заголовок, ссылка)."""
    r = requests.get(url, verify=False, timeout=10)
    r.encoding = 'utf-8'
    soup = bs(r.text, 'html.parser')

    results = []

    # Главные новости (большие карточки)
    for div in soup.find_all('div', class_='main-news_super_item_title'):
        a = div.find_parent('a') or div.find('a')
        title = div.get_text(strip=True)
        link = _abs(a['href']) if a else URL_TENGRI
        if title:
            results.append((title, link))

    # Топ-новости (список)
    for div in soup.find_all('div', class_='main-news_top_item_data'):
        a = div.find_parent('a') or div.find('a')
        title = div.get_text(strip=True)
        link = _abs(a['href']) if a else URL_TENGRI
        if title:
            results.append((title, link))

    return results


def get_news() -> str:
    """Возвращает HTML-строку со ссылками для Telegram."""
    try:
        items = parse_tengri(URL_TENGRI)
        if not items:
            return 'Новости не найдены'

        lines = ['<b>📰 Новости Tengri News:</b>\n']
        for i, (title, link) in enumerate(items[:7], 1):
            safe_title = html.escape(title)
            lines.append(f'{i}. <a href="{link}">{safe_title}</a>')

        return '\n'.join(lines)
    except Exception as e:
        return f'Ошибка при получении новостей: {html.escape(str(e))}'
