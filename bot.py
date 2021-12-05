#!./venv/bin/python3

import configparser
import logging
import os

from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import utils, url_db, user_db
import admin
import ssl

# Путь к файлу конфигурации
thisfolder = os.path.dirname(os.path.abspath(__file__))
configFilePath = os.path.join(thisfolder, 'config.ini')
config = configparser.ConfigParser()
config.read(configFilePath, encoding='utf-8')

# Парсинг файла конфигурации
token = config.get('telebot', 'token')

bot = Bot(token=token)

# Диспетчер
dp = Dispatcher(bot, storage=MemoryStorage())
# Логгирование
logging.basicConfig(level=logging.INFO)


# Проверка SSL сертификата
def check_ssl():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


commands_main = ['Добавить дело ➔',
                 'Показать дела',
                 'Удаление ➔',
                 'Настройки ➔',
                 'Администратор ➔'
                 ]
commands_delete = ['Удалить одно дело ➔',
                   'Удалить все дела ➔'
                   ]

type_delete = ['По ссылке ➔',
               'Выбрать из списка ➔'
               ]


class SelectMenu(StatesGroup):
    waiting_sel_menu = State()
    waiting_add_key = State()
    waiting_get_info = State()

    waiting_sel_key_link = State()
    waiting_key_link = State()
    waiting_sel_link = State()
    waiting_del_link = State()

    waiting_del_all_links = State()
    waiting_onoff_update = State()
    waiting_show_party = State()

    waiting_add_user = State()
    waiting_del_user = State()
    waiting_kind_link = State()
    waiting_check_link = State()


# Приветственное сообщение
@dp.message_handler(Text(equals="start", ignore_case=True))
async def start_message(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    username = message.from_user.username
    user_id = message.from_user.id
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user:
        check_name = user_db.sql_show_users()
        if check_name[0][1] == 'None':
            user_db.sql_update_name(username, user_id)
        if user['admin']:
            message_text = 'Ты являешься администратором'
            await message.answer(message_text, reply_markup=keyboard)
            await main_menu(message)
        else:
            message_text = 'Привет, ' + username + '!\n\n' \
                           + 'Набери " / " для отображения списка доступных команд или выбери из меню ⤵️'
            await message.answer_sticker('CAACAgIAAxkBAAECBF1gS6rbgBgyt_5c6ytFs8rjLhNQ3QACKAMAArVx2gaQekqHXpVKbh4E')
            await message.answer(message_text, reply_markup=keyboard)
            await main_menu(message)
    else:
        message_text = 'Извини, я закрытый бот. Пока работаю для одной компании, но я еще выйду в свет!' \
                       '\nЕсть вопросы? Обратись к @janki_wtf'
        await message.answer(message_text, reply_markup=types.ReplyKeyboardRemove())


# Меню команд
@dp.message_handler(Text(equals="меню", ignore_case=True))
async def main_menu(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    # message_id = message.message_id
    # await bot.delete_message(message.chat.id, message_id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(commands_main[0], commands_main[1])
        keyboard.add(commands_main[2], commands_main[3])
        if user['admin']:
            keyboard.add(commands_main[4])
        await message.answer('Меню:', reply_markup=keyboard)


# Слэш-команда. Спрятать клавиатуру с командами
@dp.message_handler(commands=['hide_keyboard'])
async def hide_keyboard(message: types.Message):
    await message.answer('Клавиатура спрятана', reply_markup=types.ReplyKeyboardRemove())


# Слэш-команда. Показать клавиатуру с командами
@dp.message_handler(commands=['show_keyboard'])
async def show_keyboard(message: types.Message):
    await main_menu(message)


# Слэш-команда. Показать инфо о чате
@dp.message_handler(commands=['chat_info'])
async def chat_info(message: types.Message):
    user = message.chat
    await message.answer(str(user), '')


# Адинистратор. Меню администратора
@dp.message_handler(state=SelectMenu.waiting_sel_menu)
@dp.message_handler(Text(equals="администратор ➔", ignore_case=True))
async def admin_menu(message: types.Message):
    await clean_spam(message, 1)
    await admin.admin_menu(message)


# Адинистратор. Добавление пользователя
@dp.message_handler(Text(equals="Добавить юзера", ignore_case=True))
async def add_user(message: types.Message):
    await clean_spam(message, 1)
    await admin.add_user(message)


@dp.message_handler(state=SelectMenu.waiting_add_user)
async def get_user(message: types.Message, state: FSMContext):
    await admin.get_user(message, state)


# Адинистратор. Показать всех пользователей
@dp.message_handler(Text(equals="Показать юзеров", ignore_case=True))
async def show_users(message: types.Message):
    await clean_spam(message, 1)
    await admin.show_users(message)


# Адинистратор. Удаление пользователей
@dp.message_handler(Text(equals="удалить юзера", ignore_case=True))
async def delete_user(message: types.Message):
    await clean_spam(message, 1)
    await admin.delete_user(message)


@dp.message_handler(state=SelectMenu.waiting_del_user)
async def select_link(message: types.Message, state: FSMContext):
    await admin.select_user(message, state)


# Пользователь. Просмотр всех дел
@dp.message_handler(Text(equals="показать дела", ignore_case=True))
async def show_party(message: types.Message):
    await clean_spam(message, 1)
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        if url_db.sql_count_keys() != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            for key in url_db.sql_show_party():
                row_key = types.KeyboardButton(text=str(key[0]))
                keyboard.add(row_key)
            keyboard.add(cancel_but)
            await message.answer(f'Отслеживаемые дела {url_db.sql_count_keys()}:', reply_markup=keyboard)
        else:
            await message.answer('Нет отслеживаемых дел')
        await SelectMenu.waiting_show_party.set()


@dp.message_handler(state=SelectMenu.waiting_show_party)
async def select_party(message: types.Message, state: FSMContext):
    try:
        for row in url_db.sql_show_party():
            if str(row[0][:20]).strip() == (message.text[:20]).strip():
                await message.answer(f'Информация по делу:\n{row[1]}')
    except Exception:
        await message.reply('Произошла ошибка, не смог прочитать дело. Попробуй еще раз')
    finally:
        await state.finish()
        await main_menu(message)


# Пользователь. Добавление дела
@dp.message_handler(Text(equals="добавить дело ➔", ignore_case=True))
async def add_key(message: types.Message):
    await clean_spam(message, 1)
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        try:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            keyboard.add(cancel_but)
            await SelectMenu.waiting_add_key.set()
            await message.answer('Укажи ссылку на дело:', reply_markup=keyboard)
        except Exception:
            await message.answer(
                'Произошла внутренняя ошибка. Повтори запрос.\n'
                'Если ошибка повторится, обратись к администратору'
            )


@dp.message_handler(state=SelectMenu.waiting_add_key)
async def saved_key(message: types.Message, state: FSMContext):
    global info, party
    url = message.text
    if url.lower() == 'отмена' or url.lower() == 'cancel':
        await state.finish()
        await clean_spam(message, 2)
    elif url_db.sql_check_link(url):
        await message.reply('За этим делом я уже слежу!')
    elif url[:4] == 'http':
        try:
            import url_library
            if url_library.where_url_save(url) is not False:
                await message.answer('Ожидай, добавляю дело в базу..')
                parse_data = utils.data_parser(url)
                party = parse_data[0]
                info = parse_data[1]
                user_id = message.from_user.id
                url_db.sql_new_key(party, info, url, user_id)
                await message.answer(
                    f'Дело:\n'
                    f'{party}\n'
                    f'добавлено для отслеживания!'
                )
            else:
                await message.answer('Ошибка в адресе или я c ним еще не умею работать. \nОбратись к администратору')
        except Exception:
            await message.answer('Не смог прочитать ссылку. \nПроверь правильность введенного адреса')
    else:
        await message.reply('Упс, это была не ссылка..')
    await state.finish()
    await main_menu(message)


# Пользователь. Меню удаления
@dp.message_handler(Text(equals="удаление ➔", ignore_case=True))
async def delete_menu(message: types.Message):
    await clean_spam(message, 1)
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        for butt in commands_delete:
            keyboard.add(butt)
        keyboard.add(cancel_but)
        await message.answer('Выбери способ удаления:', reply_markup=keyboard)


# Пользователь. Удаление одного дела
@dp.message_handler(Text(equals="Удалить одно дело ➔", ignore_case=True))
async def type_delete_menu(message: types.Message):
    await clean_spam(message, 2)
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        for butt in type_delete:
            keyboard.add(butt)
        keyboard.add(cancel_but)
        await message.answer('Выбери способ удаления:', reply_markup=keyboard)


# Пользователь. Удаление одного дела. По указанной ссылке
@dp.message_handler(Text(equals="По ссылке ➔", ignore_case=True))
async def delete_key_by_link(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        if url_db.sql_count_keys() != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            keyboard.add(cancel_but)
            await message.answer('Введи ссылку на дело:', reply_markup=keyboard)
            await SelectMenu.waiting_sel_key_link.set()
        else:
            await message.answer('Нет отслеживаемых дел')


@dp.message_handler(state=SelectMenu.waiting_sel_key_link)
async def select_key_link(message: types.Message, state: FSMContext):
    link = message.text
    include = [False, ]
    global sel_link
    sel_link = ['link', link]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Да', 'Отмена']
    await SelectMenu.waiting_del_link.set()
    for key in url_db.sql_show_key():
        if key[1] == link:
            include = [True, key[0]]
    if include[0] is True and link.lower() != 'отмена':
        keyboard.add(*buttons)
        await message.answer('Удаляю дело:\n (%s)?' % include[1], reply_markup=keyboard)
    elif link.lower() == 'отмена':
        await state.finish()
        await type_delete_menu(message)
    else:
        await message.answer('Ничего подходящего по указанному...', reply_markup=keyboard)
        await state.finish()
        await SelectMenu.waiting_sel_key_link.set()


# Пользователь. Удаление одного дела. По выбранному из списка участникам
@dp.message_handler(Text(equals="Выбрать из списка ➔", ignore_case=True))
async def delete_key(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        if url_db.sql_count_keys() != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            for key in url_db.sql_show_party():
                row_key = types.KeyboardButton(text=str(key[0]))
                keyboard.add(row_key)
            keyboard.add(cancel_but)
            await message.answer(
                'Отслеживаемые дела (%s)'
                '\nВыбери, что хочешь удалить:'
                % url_db.sql_count_keys(), reply_markup=keyboard
            )
            await SelectMenu.waiting_sel_link.set()
        else:
            await message.answer('Нет отслеживаемых дел')


@dp.message_handler(state=SelectMenu.waiting_sel_link)
async def select_link(message: types.Message, state: FSMContext):
    text = message.text
    if text.lower() != 'отмена':
        global sel_link
        sel_link = ['key', text]
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Да', 'Отмена']
        await SelectMenu.waiting_del_link.set()
        keyboard.add(*buttons)
        await message.answer('Удаляю?', reply_markup=keyboard)
    else:
        await state.finish()
        await type_delete_menu(message)


@dp.message_handler(state=SelectMenu.waiting_del_link)
async def del_link(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        try:
            for row in url_db.sql_show_key():
                if sel_link[0] == 'key' and row[0][:50].strip() == sel_link[1][:50].strip():
                    url_db.sql_del_key(row[0])
                elif sel_link[0] == 'link' and row[1][:50].strip() == sel_link[1][:50].strip():
                    url_db.sql_del_link(row[1])
            await message.answer('Одним меньше. Дело удалено')
            await main_menu(message)
            await state.finish()
            return
        except Exception:
            await message.reply('Произошла ошибка, дело не удалено. Попробуй еще раз')
    await state.finish()
    bot_message_id = message.message_id - 3
    user_message_id = message.message_id - 2
    await bot.delete_message(message.chat.id, bot_message_id)
    await bot.delete_message(message.chat.id, user_message_id)
    await type_delete_menu(message)


# Пользователь. Удаление всех дел
@dp.message_handler(Text(equals="Удалить все дела ➔", ignore_case=True))
async def delete_all_keys(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Да', 'Отмена']
        if url_db.sql_count_keys() != 0:
            await SelectMenu.waiting_del_all_links.set()
            keyboard.add(*buttons)
            await message.answer('Ты действительно хочешь удалить все дела?', reply_markup=keyboard)
        else:
            await message.answer('Нет отслеживаемых дел')


@dp.message_handler(state=SelectMenu.waiting_del_all_links)
async def request_text_all(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        url_db.sql_del_all_keys()
        await message.answer_sticker('CAACAgIAAxkBAAECBFtgS6pu8v0wjByDQhPnQZtBx5GfuAACJgMAArVx2gY-GQuL5xwZQB4E')
        await message.answer(
            'Все подчищено, дел больше нет.'
            '\nРасходимся', reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await state.finish()
        await delete_menu(message)
        return
    await state.finish()
    await main_menu(message)


# Пользователь. Меню настроек
@dp.message_handler(Text(equals="настройки ➔", ignore_case=True))
async def setup_menu(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        keyboard.add('Авто-обновление ➔')
        keyboard.add(cancel_but)
        await message.answer('Настройки:', reply_markup=keyboard)


# Пользователь. Меню настроек. Включение авто-обновления
@dp.message_handler(Text(equals="Авто-обновление ➔", ignore_case=True))
async def on_update(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_but = types.KeyboardButton(text='Отмена')
    update = url_db.sql_check_status(message.chat.id)
    await SelectMenu.waiting_onoff_update.set()
    if update:
        keyboard.add('Выключить')
        text = 'Авто-обновление включено, хочешь его выключить?'
    else:
        keyboard.add('Включить')
        text = 'Хочешь его включить?'
    keyboard.add(cancel_but)
    await message.answer(text, reply_markup=keyboard)


@dp.message_handler(state=SelectMenu.waiting_onoff_update)
async def set_auto_update(message: types.Message, state: FSMContext):
    if message.text.lower() == 'отмена' or message.text.lower() == 'cancel':
        await state.finish()
        await setup_menu(message)
        return
    elif message.text == 'Включить':
        url_db.sql_on_status(message.from_user.id, message.chat.id, True)
        await message.answer('Авто-обновление включено!')
    elif message.text == 'Выключить':
        url_db.sql_off_status(message.chat.id)
        await message.answer('Авто-обновление выключено!')
    await state.finish()
    await main_menu(message)


async def clean_spam(message: types.Message, count_message):
    # past_user_message_id = message.message_id - 289899
    # user_message_id = message.message_id
    # bot_message_id = message.message_id - 1
    # user_message2_id = message.message_id - 2
    # message_id = message.message_id
    # count = count_message
    count_delete_message = [message.message_id - i for i in range(count_message)]
    for one in count_delete_message:
        await bot.delete_message(message.chat.id, one)

    # await bot.delete_message(message.chat.id, user_message2_id)
    # await bot.delete_message(message.chat.id, user_message_id)
    # await bot.delete_message(message.chat.id, bot_message_id)


# Логика действий на команду Отмена
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='Отмена', ignore_case=True), state='*')
@dp.message_handler(Text(equals='back', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await clean_spam(message, 1)
    await main_menu(message)
    current_state = await state.get_state()
    await state.finish()
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)


# Запуск бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
    check_ssl()
