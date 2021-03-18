# import asyncio
import logging
from aiogram import Bot, Dispatcher, executor, types
from os import getenv
from sys import exit

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

import utils
import ssl
import database

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

# Диспетчер для бота
dp = Dispatcher(bot, storage=MemoryStorage())
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

client_status = {}

# Connect to DB
con = database.sql_connection()

# Create the table in DB
# database.sql_table(con)

commands = ['Добавить дело',
            'Показать дела',
            'Показать ссылки',
            'Инфо по делу',
            'Инфо по делам',
            'Удалить дело',
            'Удалить все дела'
            ]


class SelectMenu(StatesGroup):
    waiting_sel_menu = State()
    waiting_add_url = State()
    waiting_get_info = State()
    waiting_del_link = State()
    waiting_del_all_links = State()


# Start message
@dp.message_handler(commands=['start'])
@dp.message_handler(Text(equals="start", ignore_case=True))
async def start_message(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = commands
    keyboard.add(*button)
    message_text = 'Ага, и тебе привет, ' + message.from_user.first_name + '!\n\n' \
                   + 'Набери " / " для отображения списка доступных команд или выбери из меню ⤵️'

    await message.answer_sticker('CAACAgIAAxkBAAECBF1gS6rbgBgyt_5c6ytFs8rjLhNQ3QACKAMAArVx2gaQekqHXpVKbh4E')
    await message.answer(message_text, reply_markup=keyboard)


# Call menu
@dp.message_handler(state=SelectMenu.waiting_sel_menu)
@dp.message_handler(commands=['menu'])
@dp.message_handler(Text(equals="меню", ignore_case=True))
async def main_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = commands
    keyboard.add(*button)
    await message.answer('Меню:', reply_markup=keyboard)


# Add new url in DB
@dp.message_handler(commands=['add_url'])
@dp.message_handler(Text(equals="добавить дело", ignore_case=True))
async def process_add_url_step(message: types.Message):
    await SelectMenu.waiting_add_url.set()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    cancel_but = types.KeyboardButton(text='Отмена')
    keyboard.add(cancel_but)
    await message.answer('Укажи ссылку на дело:', reply_markup=keyboard)


@dp.message_handler(state=SelectMenu.waiting_add_url)
async def get_url(message: types.Message, state: FSMContext):
    new_url = message.text
    if new_url.lower() == 'отмена' or new_url.lower() == 'cancel':
        await main_menu(message)
        await state.finish()
        return
    if database.check_in_base(con, new_url):
        await message.reply('За этим делом я уже слежу!')
    elif new_url[:4] != 'http':
        await message.reply('Упс, это была не ссылка..')
    elif utils.where_url_save(new_url) == 'blue_site' or utils.where_url_save(new_url) == 'brown_site':
        try:
            new_url = message.text
            user_id = message.from_user.id
            database.sql_insert(con, new_url, user_id)
            await message.reply('Я взял на контроль это дело!')
            await main_menu(message)
            await state.finish()
        except Exception:
            await message.reply('Произошла ошибка, адрес не добавлен')
    else:
        await message.reply(utils.where_url_save(new_url))
    return


# Show all saved names from DB
@dp.message_handler(commands=['show_names'])
@dp.message_handler(Text(equals="показать дела", ignore_case=True))
async def show_names(message: types.Message):
    if database.count_rows_sql(con) != 0:
        await message.answer('Отслеживаемые дела (%s):' % database.count_rows_sql(con))
        for row in database.show_all_names(con):
            await message.answer("- %s" % row)
        if database.show_all_names(con)[0][0] == 'None':
            await message.answer('Информация не подгружена! \nСперва обнови информацию, нажми "Инфо по всем делам"')
    else:
        await message.answer('Нет отслеживаемых дел')


# Show all saved links from DB
@dp.message_handler(commands=['show_links'])
@dp.message_handler(Text(equals="показать ссылки", ignore_case=True))
async def show_links(message: types.Message):
    if database.count_rows_sql(con) != 0:
        await message.answer('Отслеживаемые ссылки (%s):' % database.count_rows_sql(con))
        for row in database.show_all_link(con):
            await message.answer("- %s" % row)
    else:
        await message.answer('Нет отслеживаемых ссылок')


# Request data for input link
@dp.message_handler(commands=['get_info'])
@dp.message_handler(Text(equals="инфо по делу", ignore_case=True))
async def get_info(message):
    try:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        keyboard.add(cancel_but)
        await SelectMenu.waiting_get_info.set()
        await message.answer('Укажи ссылку на дело:', reply_markup=keyboard)
    except Exception:
        await message.answer('Произошла внутренняя ошибка. Повтори запрос.\n'
                             'Если ошибка повторяется, обратись к админу')


@dp.message_handler(state=SelectMenu.waiting_get_info)
async def request_info(message: types.Message, state: FSMContext):
    url = message.text
    if url.lower() == 'отмена' or url.lower() == 'cancel':
        await main_menu(message)
        await state.finish()
        return
    if url[:4] == 'http':
        if utils.where_url_save(url) == 'blue_site' or utils.where_url_save(url) == 'brown_site':
            await message.answer('Ожидай, ищу информацию..')
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
    await state.finish()


# Request data for all links from DB
@dp.message_handler(commands=['get_info_all'])
@dp.message_handler(Text(equals="инфо по делам", ignore_case=True))
async def get_info(message: types.Message):
    try:
        if database.count_rows_sql(con) != 0:
            from_post = str()
            await message.answer('Жди, ищу информацию. Будет %s дел:' % database.count_rows_sql(con))
            for row in database.show_all_link(con):
                post = utils.data_parser(row[0])
                if utils.where_url_save(row[0]) == 'blue_site':
                    from_post = post[0][2][45:] + "\n\nДвижение по делу: \n- " + post[1][-2] + "\n" + "- " + post[1][-1]
                    database.update_info_in_base(con, row[0], post)
                elif utils.where_url_save(row[0]) == 'brown_site':
                    names = post[0][2:]
                    from_post = (', '.join(map(str, names))) + "\n\nДвижение по делу: \n- " + post[1][-2] + "\n" + "- " + \
                                post[1][-1]
                    database.update_info_in_base(con, row[0], post)
                await message.answer('\nИнформация по делу:\n' + from_post +
                                     '\n _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _')
        else:
            await message.answer('Нет отслеживаемых дел')
    except Exception:
        await message.answer('Произошла внутренняя ошибка. Повтори запрос.\n'
                             'Если ошибка повторяется, обратись к админу')

# Delete selected link from DB
@dp.message_handler(commands=['delete_link'])
@dp.message_handler(Text(equals="удалить дело", ignore_case=True))
async def delete_link(message: types.Message):
    if database.count_rows_sql(con) != 0:
        if database.show_all_names(con)[0][0] == 'None':
            await message.answer('Информация не подгружена! \nСперва обнови информацию, нажми "Инфо по всем делам"')
            await main_menu(message)
            return
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Отмена')
        keyboard.add(cancel_but)
        for row in database.show_all_names(con):
            row_link = types.KeyboardButton(text=str(row[0]))
            keyboard.add(row_link)
        await message.answer('Отслеживаемые дела (%s):' % database.count_rows_sql(con))
        await message.answer('Выбери, что хочешь удалить:', reply_markup=keyboard)
        await SelectMenu.waiting_del_link.set()
    else:
        await message.answer('Нет отслеживаемых ссылок')


@dp.message_handler(state=SelectMenu.waiting_del_link)
async def select_link(message: types.Message, state: FSMContext):
    user_text = message.text
    if user_text.lower() == 'отмена' or user_text.lower() == 'cancel':
        await main_menu(message)
        await state.finish()
        return
    else:
        for row in database.show_all_names(con):
            try:
                if row[0].strip() == user_text.strip():
                    database.delete_link(con, row[0])
                    await message.answer('Одним меньше. Дело удалено')
                    await main_menu(message)
                    await state.finish()
                    return
            except Exception:
                await message.reply('Произошла ошибка, дело не удалено. Попробуй еще раз')


# Delete all links
@dp.message_handler(commands=['delete_links'])
@dp.message_handler(Text(equals="удалить все дела", ignore_case=True))
async def delete_all_links(message: types.Message):
    await SelectMenu.waiting_del_all_links.set()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ['Да', 'Нет']
    if database.count_rows_sql(con) != 0:
        keyboard.add(*buttons)
        await message.answer('Ты действительно хочешь удалить все дела?', reply_markup=keyboard)
    else:
        await message.answer('Нет отслеживаемых дел')


@dp.message_handler(state=SelectMenu.waiting_del_all_links)
async def request_text_all(message: types.Message, state: FSMContext):
    if message.text.lower() == 'да':
        database.delete_all_link(con)
        await message.answer_sticker('CAACAgIAAxkBAAECBFtgS6pu8v0wjByDQhPnQZtBx5GfuAACJgMAArVx2gY-GQuL5xwZQB4E')
        await message.answer('Все следы подчищены. База пуста', reply_markup=types.ReplyKeyboardRemove())
    else:
        await state.finish()
        await main_menu(message)
        return
    await state.finish()
    await main_menu(message)


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await main_menu(message)
    current_state = await state.get_state()
    await state.finish()
    if current_state is None:
        return
    logging.info('Cancelling state %r', current_state)


# Регистрация команд, отображаемых в интерфейсе Telegram
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/menu", description="Меню команд"),
        BotCommand(command="/add_url", description="Добавить дело для отслеживания"),
        BotCommand(command="/show_names", description="Показать отслеживаемые дела"),
        BotCommand(command="/show_links", description="Показать отслеживаемые ссылки на дела"),
        BotCommand(command="/get_info", description="Запросить информацию по частному делу"),
        BotCommand(command="/get_info_all", description="Запросить информацию по всем делам"),
        BotCommand(command="/delete_link", description="Удалить дело из отслеживания"),
        BotCommand(command="/delete_all_links", description="Удалить все дела из отслеживания")
    ]
    await bot.set_my_commands(commands)
    # Install commands of bot with slash
    await set_commands(bot)

if __name__ == "__main__":
    # Run hte bot
    executor.start_polling(dp, skip_updates=True)
