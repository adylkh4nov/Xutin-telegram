import requests
import warnings
from bs4 import BeautifulSoup as b

warnings.filterwarnings('ignore', message='Unverified HTTPS request')

URL_Tengri = 'https://tengrinews.kz/'


def parse_tengri(url):
    r = requests.get(url, verify=False, timeout=10)
    r.encoding = 'utf-8'
    soup = b(r.text, 'html.parser')

    # Главные новости (большие карточки)
    super_items = soup.find_all('div', class_='main-news_super_item_title')
    # Топ новости (список справа)
    top_items = soup.find_all('div', class_='main-news_top_item_data')

    news_list = []
    for item in super_items:
        text = item.get_text(strip=True)
        if text:
            news_list.append(text)
    for item in top_items:
        text = item.get_text(strip=True)
        if text:
            news_list.append(text)

    return news_list


def get_news():
    try:
        items = parse_tengri(URL_Tengri)
        if not items:
            return 'Новости не найдены'
        result = '📰 *Новости Tengri News:*\n\n'
        for i, item in enumerate(items[:7], 1):
            result += f'{i}. {item}\n\n'
        return result
    except Exception as e:
        return f'Ошибка при получении новостей: {e}'
