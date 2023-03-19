import os
import time
import logging
import sys
from http import HTTPStatus

import requests
import pprint
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

timestamp = int(time.time())

def get_api_answer(timestamp: int):
    """Получаем ответ от Яндекс.Домашка(тм)."""
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return response.json()

print(get_api_answer(timestamp))

dict = {'homeworks': [], 'current_date': 1669653626}
homeworks = dict.get('homeworks')
print(homeworks)

if not homeworks:
    print('yes! the list is empty.')