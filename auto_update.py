#!./venv/bin/python3

import configparser
import datetime
import telegram
import os
import url_db
import utils
from pathos.multiprocessing import ProcessingPool as Pool

# Путь к файлу конфигурации
thisfolder = os.path.dirname(os.path.abspath(__file__))
configFilePath = os.path.join(thisfolder, 'config.ini')
config = configparser.ConfigParser()
config.read(configFilePath, encoding='utf-8')

# Парсинг файла конфигурации
token = config.get('telebot', 'token')


# Парсинг каждого остлеживаемого дела в базе
def check_key(key):
    count_keys = url_db.sql_count_keys()

    if count_keys != 0:
        db_info = key[1]
        link = key[2]
        parse_data = utils.data_parser(link)
        if parse_data['success']:
            response = parse_data['response']
            key = response[0]
            up_info = response[1]
            if up_info != db_info:
                url_db.sql_update_info(up_info, link)
                print('link is updated')
                return {'bool': True,
                        'link': link,
                        'update': f"{key}\n{up_info}",
                        'success': f"{parse_data['response'][0]}\n"
                                   f"{parse_data['response'][1]}\n"}
            print('link is ok')
        else:
            print('no success',link)
            return {'bool': False, 'link': link}
    return {'bool': None}


# Многопроцессорность и обработка результатов функции check_key()
def get_result():
    success = []
    errors = []
    updates = {'success': success, 'errors': errors}

    keys = url_db.sql_saved_keys()
    list_keys = [key for key in keys]
    pool = Pool()
    results = pool.map(check_key, list_keys)
    for key in results:
        if key['bool']:
            success.append(key['update'])
        elif key['bool'] is False:
            errors.append(key['link'])
        else:
            continue
    pool.close()
    pool.join()
    return updates


# Eжедневный парсинг сайтов судов
def func_auto_update():
    count_keys = url_db.sql_count_keys()
    chats = url_db.sql_all_status()
    news = get_result()

    error_keys = news['errors']
    success_keys = news['success']
    time = datetime.datetime.now()
    now = time.strftime("%Y-%m-%d")

    # Рассылка результатов по подписавшимся на обновления чатам
    for chat_id in chats:
        for success in success_keys:
            send_message(
                chat_id[0], f"Обновление дела от {now}:\n"
                            f"{success}"
            )

        if len(error_keys) > 5:
            error_message = "\n----------------\n".join(error_keys)
            send_message(chat_id[0], error_message)
        else:
            for error in error_keys:
                send_message(
                    chat_id[0], f"{now}: Не обновилось дело:\n "
                                f"{error}"
                )

    for chat_id in chats:
        info_message = f'Ежедневный апдейт от {now} завершен:'
        if len(success_keys) == 0:
            info_message += '\nНовой информации по делам нет'
        else:
            info_message += f'\nОбновлено {len(success_keys)} дел(-а).'
        if len(error_keys) != 0:
            info_message += '\nНе все дела смог проверить:\n' \
                            f'Успешно проверенных: {count_keys - len(error_keys)} из ' \
                            f'{count_keys}\n'
        send_message(chat_id[0], info_message)
    return


# Отправка сообщений в чат
def send_message(chat_id, message):
    timeout = 30
    request = telegram.utils.request.Request(read_timeout=timeout)
    bot = telegram.Bot(token, request=request)
    parse_mode = None
    silent = False
    disable_web_page_preview = False

    return bot.send_message(
        chat_id=chat_id, text=message, parse_mode=parse_mode, disable_notification=silent,
        disable_web_page_preview=disable_web_page_preview
    )


if __name__ == "__main__":
    func_auto_update()
