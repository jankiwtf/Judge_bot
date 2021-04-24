import logging
from aiogram import Bot, Dispatcher, executor, types
from os import getenv

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
# url_db.sql_create_keys_table(con) # New keys table
# user_db.sql_create_user_table(con) # New users table

commands_main = ['Добавить дело ➔',
                 'Показать дела',
                 'Инфо по всем делам',
                 'Движения по делам',
                 'Удаление ➔',
                 '/admin_panel ➔'
                 ]
commands_delete = ['Удалить одно дело',
                   'Удалить все дела'
                   ]


class SelectMenu(StatesGroup):
    waiting_sel_menu = State()
    waiting_add_key = State()
    waiting_add_user = State()
    waiting_get_info = State()
    waiting_del_link = State()
    waiting_del_user = State()
    waiting_del_all_links = State()


# Start message
@dp.message_handler(commands=['start'])
@dp.message_handler(Text(equals="start", ignore_case=True))
async def start_message(message: types.Message):
    user = user_db.sql_init_user(con, message.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if user:
        if user['admin']:
            message_text = 'Ты являешься администратором'
            await message.answer(message_text, reply_markup=keyboard)
            await main_menu(message)
        else:
            message_text = 'Ага, и тебе привет, ' + message.from_user.first_name + '!\n\n' \
                           + 'Набери " / " для отображения списка доступных команд или выбери из меню ⤵️'
            await message.answer_sticker('CAACAgIAAxkBAAECBF1gS6rbgBgyt_5c6ytFs8rjLhNQ3QACKAMAArVx2gaQekqHXpVKbh4E')
            await message.answer(message_text, reply_markup=keyboard)
            await main_menu(message)
    else:
        message_text = 'Извини, я закрытый бот. Пока я работаю для одной компании, но я еще выйду в свет!' \
                       '\nЕсть вопросы? Обратись к администратору @janki_wtf'
        await message.answer(message_text, reply_markup=types.ReplyKeyboardRemove())


# Call menu
@dp.message_handler(commands=['menu'])
@dp.message_handler(Text(equals="меню", ignore_case=True))
async def main_menu(message: types.Message):
    user = user_db.sql_init_user(con, message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(commands_main[0], commands_main[1])
        keyboard.add(commands_main[2], commands_main[3])
        keyboard.add(commands_main[4])
        if user['admin']:
            keyboard.add(commands_main[5])
        await message.answer('Меню:', reply_markup=keyboard)


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


# Delete user from DB
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
    user = user_db.sql_init_user(con, message.from_user.id)
    if user['verif']:
        if url_db.sql_count_keys(con) != 0:
            await message.answer('Отслеживаемые дела (%s):' % url_db.sql_count_keys(con))
            for row in url_db.sql_show_party(con):
                await message.answer("- %s" % row)
            if url_db.sql_show_party(con)[0][0] == 'None':
                await message.answer('Информация не подгружена! \nСперва обнови информацию, нажми "Инфо по всем делам"')
        else:
            await message.answer('Нет отслеживаемых дел')


@dp.message_handler(state=SelectMenu.waiting_get_info)
async def request_info(message: types.Message, state: FSMContext):
    url = message.text
    if url.lower() == 'отмена' or url.lower() == 'cancel':
        await main_menu(message)
        await state.finish()
        return
    if url[:4] == 'http':
        if utils.where_url_save(url) == 'blue_site' or utils.where_url_save(url) == 'brown_site':
            await message.answer('Ожидай, ищу информацию по делу..')
            post = utils.data_parser(url)
            await message.answer('Информация по делу:')
            if utils.where_url_save(url) == 'blue_site':
                from_post = post[0][2][45:] + "\n\nДвижение по делу: \n- " + post[1][-2] + "\n" + "- " + post[1][-1]
                await message.answer(from_post)
            elif utils.where_url_save(url) == 'brown_site':
                names = post[0][2:]
                from_post = ('\n'.join(map(str, names))) + "\n\nДвижение по делу: \n- " + post[1][-2] + "\n" + "- " + \
                            post[1][-1]
                await message.answer(from_post)
            else:
                await message.answer(utils.where_url_save(url))
                return
        else:
            await message.answer(utils.where_url_save(url))
    else:
        await message.reply('Упс, это была не ссылка..')
        return
    await main_menu(message)
    await state.finish()


# Add new key in DB
@dp.message_handler(commands=['add_key'])
@dp.message_handler(Text(equals="добавить дело ➔", ignore_case=True))
async def add_key(message: types.Message):
    user = user_db.sql_init_user(con, message.from_user.id)
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
    await state.finish()
    url = message.text
    if url.lower() == 'отмена' or url.lower() == 'cancel':
        await main_menu(message)
    elif url_db.sql_check_link(con, url):
        await message.reply('За этим делом я уже слежу!')
    elif url[:4] == 'http':
        if utils.where_url_save(url) == 'blue_site' or utils.where_url_save(url) == 'brown_site':
            await message.answer('Ожидай, ищу информацию..')
            post = utils.data_parser(url)
            if utils.where_url_save(url) == 'blue_site':
                party = post[0][2][45:]
                info = f'- {post[1][-2]}\n- {post[1][-1]}'
            elif utils.where_url_save(url) == 'brown_site':
                party = post[0][2] + "," + post[0][3]
                info = f'- {post[1][-2]},\n- {post[1][-1]}'
            user_id = message.from_user.id
            url_db.sql_new_key(con, party, info, url, user_id)
            await message.answer('Дело добавлено для отслеживания!')
        else:
            await message.answer(utils.where_url_save(url))
    else:
        await message.reply('Упс, это была не ссылка..')
    await main_menu(message)


# Request data for all links from DB
@dp.message_handler(commands=['get_info'])
@dp.message_handler(Text(equals="инфо по всем делам", ignore_case=True))
async def get_info(message: types.Message):
    user = user_db.sql_init_user(con, message.from_user.id)
    if user['verif']:
        try:
            if url_db.sql_count_keys(con) != 0:
                for key in url_db.sql_saved_keys(con):
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
    count_keys = url_db.sql_count_keys(con)
    count_not_update = 0
    user = user_db.sql_init_user(con, message.from_user.id)
    if user['verif']:
        try:
            if count_keys != 0:
                await message.answer(f'Ожидай, проверяю информацию по {count_keys} делам..'
                                     f'\nПожалуйста, не отвлекай меня.'
                                     f'\nЯ сообщу, как закончу ')
                for key in url_db.sql_saved_keys(con):
                    db_party = key[0]
                    db_info = key[1]
                    link = key[2]
                    post = utils.data_parser(link)
                    if utils.where_url_save(link) == 'blue_site':
                        up_info = f'- {post[1][-2]}\n- {post[1][-1]}'
                    elif utils.where_url_save(link) == 'brown_site':
                        up_info = f'- {post[1][-2]},\n- {post[1][-1]}'
                    if up_info == db_info:
                        count_not_update += 1
                    else:
                        url_db.sql_update_info(con, up_info, link)
                        await message.answer(f"Информация обновлена по делу:\n "
                                             f"{db_party}\n "
                                             f"{up_info}\n _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _")

                    if count_keys == count_not_update:
                        await message.answer('Новой информации по делам нет')
                        return
                await message.answer('Готово, я закончил. Все дела проверены!')
            else:
                await message.answer('Нет отслеживаемых дел')
        except Exception:
            await message.answer('Произошла внутренняя ошибка. Повтори запрос.\n'
                                 'Если ошибка повторится, обратись к администратору')


# Delete menu
@dp.message_handler(Text(equals="удаление ➔", ignore_case=True))
async def delete_menu(message: types.Message):
    user = user_db.sql_init_user(con, message.from_user.id)
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
    user = user_db.sql_init_user(con, message.from_user.id)
    if user['verif']:
        if url_db.sql_count_keys(con) != 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            cancel_but = types.KeyboardButton(text='Отмена')
            for row in url_db.sql_show_party(con):
                row_link = types.KeyboardButton(text=str(row[0]))
                keyboard.add(row_link)
            keyboard.add(cancel_but)
            await message.answer('Отслеживаемые дела (%s)'
                                 '\nВыбери, что хочешь удалить:'
                                 % url_db.sql_count_keys(con), reply_markup=keyboard)
            await SelectMenu.waiting_del_link.set()
        else:
            await message.answer('Нет отслеживаемых ссылок')


@dp.message_handler(state=SelectMenu.waiting_del_link)
async def select_link(message: types.Message, state: FSMContext):
    text = message.text
    if text.lower() == 'отмена' or text.lower() == 'cancel':
        await delete_menu(message)
        await state.finish()
        return
    else:
        for row in url_db.sql_show_party(con):
            try:
                if row[0].strip() == text.strip():
                    url_db.sql_del_key(con, row[0])
                    await message.answer('Одним меньше. Дело удалено')
                    await main_menu(message)
                    await state.finish()
                    return
            except Exception:
                await message.reply('Произошла ошибка, дело не удалено. Попробуй еще раз')


# Delete all links
@dp.message_handler(commands=['delete_all_keys'])
@dp.message_handler(Text(equals="удалить все дела", ignore_case=True))
async def delete_all_keys(message: types.Message):
    user = user_db.sql_init_user(con, message.from_user.id)
    if user['verif']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Да', 'Нет']
        if url_db.sql_count_keys(con) != 0:
            await SelectMenu.waiting_del_all_links.set()
            keyboard.add(*buttons)
            await message.answer('Ты действительно хочешь удалить все дела?', reply_markup=keyboard)
        else:
            await message.answer('Нет отслеживаемых дел')


@dp.message_handler(state=SelectMenu.waiting_del_all_links)
async def request_text_all(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        url_db.sql_del_all_keys(con)
        await message.answer_sticker('CAACAgIAAxkBAAECBFtgS6pu8v0wjByDQhPnQZtBx5GfuAACJgMAArVx2gY-GQuL5xwZQB4E')
        await message.answer('Ты счастливый человек!'
                             '\nБаза пуста. Расходимся', reply_markup=types.ReplyKeyboardRemove())
    else:
        await state.finish()
        await delete_menu(message)
        return
    await state.finish()
    await main_menu(message)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
@dp.message_handler(Text(equals='back', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await main_menu(message)
    current_state = await state.get_state()
    await state.finish()
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)


if __name__ == "__main__":
    # Run bot
    executor.start_polling(dp, skip_updates=True)
