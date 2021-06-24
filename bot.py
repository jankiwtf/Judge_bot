import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from os import getenv

import datetime
import aioschedule

from sys import exit
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import utils, url_db, user_db
import admin
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

bot_token = getenv("BOT_TOKEN")

if not bot_token:
    exit("Error: no token provided")
bot = Bot(token=bot_token)

# Dispatch on
dp = Dispatcher(bot, storage=MemoryStorage())
# Log on
logging.basicConfig(level=logging.INFO)

client_status = {}

# Connect to DB
con = url_db.sql_connection()

# Create new tables in DB
url_db.sql_create_keys_table()  # New keys table
# user_db.sql_create_user_table() # New users table
url_db.sql_create_upd_stat_table()  # Update status table

commands_main = ['Добавить дело ➔',
                 'Показать дела',
                 'Инфо по всем делам',
                 'Движения по делам',
                 'Удаление ➔',
                 'Настройки ➔',
                 '/admin_panel ➔'
                 ]
commands_delete = ['Удалить одно дело',
                   'Удалить все дела'
                   ]


class SelectMenu(StatesGroup):
    waiting_sel_menu = State()
    waiting_add_key = State()
    waiting_get_info = State()
    waiting_sel_link = State()
    waiting_del_link = State()
    waiting_del_all_links = State()
    waiting_onoff_update = State()
    waiting_show_party = State()

    waiting_add_user = State()
    waiting_del_user = State()
    waiting_kind_link = State()
    waiting_check_link = State()


# Start message
@dp.message_handler(commands=['start'])
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
            message_text = 'Ага, и тебе привет, ' + username + '!\n\n' \
                           + 'Набери " / " для отображения списка доступных команд или выбери из меню ⤵️'
            await message.answer_sticker('CAACAgIAAxkBAAECBF1gS6rbgBgyt_5c6ytFs8rjLhNQ3QACKAMAArVx2gaQekqHXpVKbh4E')
            await message.answer(message_text, reply_markup=keyboard)
            await main_menu(message)
    else:
        message_text = 'Извини, я закрытый бот. Пока работаю для одной компании, но я еще выйду в свет!' \
                       '\nЕсть вопросы? Обратись к администратору @janki_wtf'
        await message.answer(message_text, reply_markup=types.ReplyKeyboardRemove())


# Call menu
@dp.message_handler(commands=['menu'])
@dp.message_handler(Text(equals="меню", ignore_case=True))
async def main_menu(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    # message_id = message.message_id
    # await bot.delete_message(message.chat.id, message_id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(commands_main[0], commands_main[1])
        keyboard.add(commands_main[2], commands_main[3])
        keyboard.add(commands_main[4])
        keyboard.add(commands_main[5])
        if user['admin']:
            keyboard.add(commands_main[6])
        await message.answer('Меню:', reply_markup=keyboard)


# hide keyboard
@dp.message_handler(commands=['hide'])
async def hide_keyboard(message: types.Message):
    await message.answer('The keyboard is hidden', reply_markup=types.ReplyKeyboardRemove())


# hide keyboard
@dp.message_handler(commands=['visible'])
async def show_keyboard(message: types.Message):
    await main_menu(message)


# Chat info
@dp.message_handler(commands=['chat_info'])
async def chat_info(message: types.Message):
    user = message.chat
    await message.answer(str(user), '')


# Admin. Admin panel
@dp.message_handler(state=SelectMenu.waiting_sel_menu)
@dp.message_handler(Text(equals="/admin_panel ➔", ignore_case=True))
async def admin_menu(message: types.Message):
    await admin.admin_menu(message)


# Admin. New user
@dp.message_handler(Text(equals="/add_user", ignore_case=True))
async def add_user(message: types.Message):
    await admin.add_user(message)
@dp.message_handler(state=SelectMenu.waiting_add_user)
async def get_user(message: types.Message, state: FSMContext):
    await admin.get_user(message, state)


# Admin. Show all users
@dp.message_handler(Text(equals="/show_users", ignore_case=True))
async def show_users(message: types.Message):
    await admin.show_users(message)


# Admin. Delete user from DB
@dp.message_handler(Text(equals="/delete_user", ignore_case=True))
async def delete_user(message: types.Message):
    await admin.delete_user(message)
@dp.message_handler(state=SelectMenu.waiting_del_user)
async def select_link(message: types.Message, state: FSMContext):
    await admin.select_user(message, state)


# Show all party
@dp.message_handler(commands=['show_party'])
@dp.message_handler(Text(equals="показать дела", ignore_case=True))
async def show_party(message: types.Message):
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

# Add new key in DB
@dp.message_handler(commands=['add_key'])
@dp.message_handler(Text(equals="добавить дело ➔", ignore_case=True))
async def add_key(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        try:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            keyboard.add(cancel_but)
            await SelectMenu.waiting_add_key.set()
            await message.answer('Укажи ссылку на дело:', reply_markup=keyboard)
        except Exception:
            await message.answer('Произошла внутренняя ошибка. Повтори запрос.\n'
                                 'Если ошибка повторится, обратись к администратору')

@dp.message_handler(state=SelectMenu.waiting_add_key)
async def saved_key(message: types.Message, state: FSMContext):
    global info, party
    url = message.text
    if url.lower() == 'отмена' or url.lower() == 'cancel':
        await state.finish()
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
                await message.answer(f'Дело:\n'
                                     f'{party}\n'
                                     f'добавлено для отслеживания!')
            else:
                await message.answer('Ошибка в адресе или я c ним еще не умею работать. \nОбратись к администратору')
        except Exception:
            await message.answer('Не смог прочитать ссылку. \nПроверь правильность введенного адреса')
    else:
        await message.reply('Упс, это была не ссылка..')
    await state.finish()
    await main_menu(message)


# Request data for all links from DB
@dp.message_handler(commands=['get_info'])
@dp.message_handler(Text(equals="инфо по всем делам", ignore_case=True))
async def get_info(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        try:
            if url_db.sql_count_keys() != 0:
                for key in url_db.sql_saved_keys():
                    party = key[0]
                    info = key[1]
                    await message.answer(f"Информация по делу:\n "
                                         f"{party}\n "
                                         f"{info}\n _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")
            else:
                await message.answer('Нет отслеживаемых дел')
        except Exception:
            await message.answer('Произошла внутренняя ошибка. Повтори запрос.\n'
                                 'Если ошибка повторится, обратись к администратору')


# Update info in keys
@dp.message_handler(commands=['update_info'])
@dp.message_handler(Text(equals="Движения по делам", ignore_case=True))
async def update_info(message: types.Message):
    global up_info
    count_keys = url_db.sql_count_keys()
    chat_id = message.chat.id
    user = user_db.sql_init_user(message.from_user.id)
    chats = url_db.sql_all_status()
    count_not_update = 0
    time = datetime.datetime.now()
    now = time.strftime("%Y-%m-%d")
    if user['verif']:
        if count_keys != 0:
            for key in url_db.sql_saved_keys():
                db_info = key[1]
                link = key[2]
                try:
                    parse_data = utils.data_parser(link)
                    await asyncio.sleep(5)
                    up_info = parse_data[1]
                    if up_info != db_info:
                        url_db.sql_update_info(up_info, link)
                        mess_update = f"Обновление дела от {now}:\n\n" \
                                      f"{parse_data[0]}\n" \
                                      f"{parse_data[1]}\n" \
                                      f"_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _"
                        await bot.send_message(chat_id, mess_update)
                        if chats != 0:
                            for chat in chats:
                                if chat[0] != chat_id:
                                    await bot.send_message(chat[0], mess_update)
                    else:
                        count_not_update += 1
                except Exception:
                    await message.answer(f'Не смог проверить дело:\n {link}')
            if count_keys == count_not_update:
                await message.answer('Новой информации по делам нет')
            else:
                await message.answer('Готово, все дела проверены!')
        else:
            await message.answer('Нет отслеживаемых дел')


# Delete menu
@dp.message_handler(Text(equals="удаление ➔", ignore_case=True))
async def delete_menu(message: types.Message):
    await clean_spam(message)
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        for butt in commands_delete:
            keyboard.add(butt)
        keyboard.add(cancel_but)
        await message.answer('Выбери способ удаления:', reply_markup=keyboard)


# Delete key from DB
@dp.message_handler(commands=['delete_key'])
@dp.message_handler(Text(equals="удалить одно дело", ignore_case=True))
async def delete_key(message: types.Message):
    await clean_spam(message)
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        if url_db.sql_count_keys() != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            for key in url_db.sql_show_party():
                row_key = types.KeyboardButton(text=str(key[0]))
                keyboard.add(row_key)
            keyboard.add(cancel_but)
            await message.answer('Отслеживаемые дела (%s)'
                                 '\nВыбери, что хочешь удалить:'
                                 % url_db.sql_count_keys(), reply_markup=keyboard)
            await SelectMenu.waiting_sel_link.set()
        else:
            await message.answer('Нет отслеживаемых ссылок')


@dp.message_handler(state=SelectMenu.waiting_sel_link)
async def select_link(message: types.Message, state: FSMContext):
    text = message.text
    # await clean_spam(message)
    if text.lower() != 'отмена':
        global sel_link
        sel_link = text
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Да', 'Отмена']
        await SelectMenu.waiting_del_link.set()
        keyboard.add(*buttons)
        await message.answer('Удаляю?', reply_markup=keyboard)
    else:
        await cancel_handler(message, state)


@dp.message_handler(state=SelectMenu.waiting_del_link)
async def del_link(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        for row in url_db.sql_show_party():
            try:
                if row[0][:50].strip() == sel_link[:50].strip():
                    url_db.sql_del_key(row[0])
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
    await delete_key(message)


# Delete all links
@dp.message_handler(commands=['delete_all_keys'])
@dp.message_handler(Text(equals="удалить все дела", ignore_case=True))
async def delete_all_keys(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Да', 'Нет']
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
        await message.answer('Все подчищено, дел больше нет.'
                             '\nРасходимся', reply_markup=types.ReplyKeyboardRemove())
    else:
        await state.finish()
        await delete_menu(message)
        return
    await state.finish()
    await main_menu(message)


# Setup menu
@dp.message_handler(Text(equals="настройки ➔", ignore_case=True))
async def setup_menu(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        keyboard.add('Авто-обновление ➔')
        keyboard.add(cancel_but)
        await message.answer('Настройки:', reply_markup=keyboard)


# Setup menu
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


async def auto_update():
    global up_info, chat_id
    count_keys = url_db.sql_count_keys()
    chats = url_db.sql_all_status()
    count_error = 0
    count_update = 0
    time = datetime.datetime.now()
    now = time.strftime("%Y-%m-%d")
    if count_keys != 0:
        for key in url_db.sql_saved_keys():
            db_info = key[1]
            link = key[2]
            try:
                parse_data = utils.data_parser(link)
                up_info = parse_data[1]
                if up_info != db_info:
                    count_update += 1
                    url_db.sql_update_info(up_info, link)
                    for chat_id in chats:
                        await bot.send_message(chat_id[0], f"Обновление дела от {now}:\n"
                                                           f"{parse_data[0]}\n "
                                                           f"{parse_data[1]}\n "
                                                           f"_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")
            except Exception:
                for chat_id in chats:
                    await bot.send_message(chat_id[0], f'{now}: Не обновилось дело:\n {link}')
                count_error += 1
        for chat_id in chats:
            info_message = f'Ежедневный апдейт от {now} завершен:'
            if count_update == 0:
                info_message += '\nНовой информации по делам нет'
            else:
                info_message += f'\nОбновлено {count_update} дел.'
            if count_error != 0:
                info_message += '\nНе все дела смог проверить:\n' \
                                f'Успешно проверенных: {url_db.sql_count_keys() - count_error} из ' \
                                f'{url_db.sql_count_keys()}\n'
            await bot.send_message(chat_id[0], info_message)


async def scheduler():
    chats = url_db.sql_all_status()
    if chats != 0:
        aioschedule.every().day.at("09:00").do(auto_update)
        aioschedule.every().day.at("07:00").do(straighten_back)
        aioschedule.every().day.at("11:00").do(straighten_back)
        while True:
            await aioschedule.run_pending()
            await asyncio.sleep(1)


async def on_auto_update(_):
    asyncio.create_task(scheduler())

@dp.message_handler(Text(equals="зарядка", ignore_case=True))
async def straighten_back():
    await asyncio.sleep(random_time())
    chats = url_db.sql_all_status()
    info_message = ('Выпрямление спинки через:', ' 3..', '2..', '1..')
    for chat_id in chats:
        for mess in info_message:
            await bot.send_message(chat_id[0], mess)
            await asyncio.sleep(1)
        await bot.send_sticker(chat_id[0], 'CAACAgIAAxkBAAECdghg0yLdkz8f2TUjHoVHb1MMXUPVwgACuxEAAo9amUoSKBCkDQWMUh8E')


def random_time():
    import random
    minutes = random.randint(0, 61) * 60
    hour = (random.randint(1, 4)) * 60 * 60
    return hour + minutes


async def clean_spam(message: types.Message):
    # past_user_message_id = message.message_id - 2
    user_message_id = message.message_id
    bot_message_id = message.message_id - 1
    # await bot.delete_message(message.chat.id, past_user_message_id)
    # await bot.delete_message(message.chat.id, bot_message_id)
    await bot.delete_message(message.chat.id, bot_message_id)
    await bot.delete_message(message.chat.id, user_message_id)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='Отмена', ignore_case=True), state='*')
@dp.message_handler(Text(equals='back', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await main_menu(message)
    current_state = await state.get_state()
    await state.finish()
    await clean_spam(message)
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)

# Run bot
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_auto_update)
