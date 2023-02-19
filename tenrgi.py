import requests
from bs4 import BeautifulSoup as b
URL_Tengri = 'https://tengrinews.kz/'

def parse_tengri(url):
    r = requests.get(url)
    soup = b(r.text, 'html.parser')
    news = soup.find_all('div', class_='tn-tape-item tn-popular')
    clear_news = [c.text for c in news]

    return clear_news[0]
news = parse_tengri(URL_Tengri)