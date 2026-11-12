import requests 

from config import PROXY_LIST_URL
# Загрузка списка прокси


def get_proxies():
    # сначала пробуем получить ответ
    response = requests.get(PROXY_LIST_URL,timeout=15)

    # пытаемся получить статус ответа(если проблема оно само выкинет из функции)
    response.raise_for_status()

    print (response.text.splitlines())

    return response.text.splitlines();

