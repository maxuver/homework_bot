import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяем наличие токенов, ID чата."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: telegram.bot.Bot, message: str):
    """Направляем сообщение в телеграм чат."""
    logger.debug('Начата отправка сообщения в Telegram')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError:
        logger.error('Что-то не так, сообщение в телеграм не отправлено!')
    else:
        logger.debug('Сообщение в телеграм отправлено успешно!')


def get_api_answer(timestamp: int):
    """Получаем ответ от Яндекс.Домашка."""
    params = {'from_date': timestamp}
    logger.debug('Начата отправка GET запроса к Яндекс.Домашка')
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            response.raise_for_status()
        logger.info('Ответ на запрос к API: 200 OK')
        return response.json()
    except requests.exceptions.RequestException:
        logger.error('Ошибка при запросе к Яндекс.Домашка')


def check_response(response: dict):
    """Проверяем ответ от Яндекс.Домашка."""
    if not isinstance(response, dict):
        raise TypeError('В ответе API домашки не содержится словарь')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('В ответе API домашки нет ключей <homeworks>'
                       'или <current_date>')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('В ответе API домашки под ключом'
                        '`homeworks` данные приходят не в виде списка')
    return homeworks


def parse_status(homework: dict):
    """Извлекаем из ответа от Яндекс.Домашка информацию о статусе."""
    if 'status' not in homework:
        raise KeyError('В ответе API домашки нет ключа <status>')
    if 'homework_name' not in homework:
        raise KeyError('В ответе API домашки нет ключа <homework_name>')
    homework_name = homework[('homework_name')]
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Не поддерживаемый статус')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return ('Изменился статус проверки работы '
            f'"{homework_name}". {verdict}')


def main():
    """Основная логика работы бота."""
    logger.info('Бот запущен')
    message_to_check_the_token = 'Проверьте Токены API, ID чата!'
    if not check_tokens():
        logger.critical(message_to_check_the_token)
        sys.exit(message_to_check_the_token)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    message_check = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homework_info = check_response(response)
            if homework_info:
                message = parse_status(homework_info[0])
                if message_check != message:
                    send_message(bot, message)
                    message_check = message
            logger.debug('Изменений нет. Обновлю статус через 10 минут.')
        except Exception as error:
            if message_check != message:
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)
                message_check = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
