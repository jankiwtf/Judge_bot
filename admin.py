import configparser
import logging
import os
from aiogram import types
from aiogram.dispatcher import FSMContext

import bot
import telegram
import url_db, user_db
from bot import SelectMenu

# Путь к файлу конфигурации
thisfolder = os.path.dirname(os.path.abspath(__file__))
configFilePath = os.path.join(thisfolder, 'config.ini')
config = configparser.ConfigParser()
config.read(configFilePath, encoding='utf-8')

# Парсинг файла конфигурации
token = config.get('telebot', 'token')

# Connect to DB
con = url_db.sql_connection()

commands_admin = ['Добавить юзера',
                  'Показать юзеров',
                  'Удалить юзера',
                  'Отправить сообщение'
                  ]


# Admin panel
async def admin_menu(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['admin']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Back')
        keyboard.add(cancel_but)
        for command in commands_admin:
            keyboard.add(command)
        await message.answer('Admin commands:', reply_markup=keyboard)


# Add new user
async def add_user(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['admin']:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='Back')
        keyboard.add(cancel_but)
        await SelectMenu.waiting_add_user.set()
        await message.answer("Enter user's id:", reply_markup=keyboard)

async def get_user(message: types.Message, state: FSMContext):
    user_id = message.text
    if user_id.lower() == 'back':
        await admin_menu(message)
        await state.finish()
    elif user_id.isdigit():
        user = user_db.sql_init_user(user_id)
        if user is False:
            user_db.sql_new_user(user_id)
            await message.reply('User is added')
            await admin_menu(message)
            await state.finish()
        else:
            await message.reply('Error! User is already added')
    else:
        await message.reply('Error! User is not added')


async def show_users(message: types.Message):
    user = user_db.sql_init_user(message.from_user.id)
    if user['admin']:
        if url_db.sql_count_keys() != 0:
            db_users = user_db.sql_show_users()
            await message.answer('Registered users (%s):' % user_db.sql_count_users())
            await message.answer(db_users)
        else:
            await message.answer('No registered users')


async def delete_user(message: types.Message):
    if user_db.sql_count_users() != 1:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        cancel_but = types.KeyboardButton(text='<-Back')
        keyboard.add(cancel_but)
        for row in user_db.sql_show_users()[1:]:
            row_link = types.KeyboardButton(text=str(row))
            keyboard.add(row_link)
        await message.answer('Select user:', reply_markup=keyboard)
        await SelectMenu.waiting_del_user.set()
    else:
        await message.answer('No saved users')


async def select_user(message: types.Message, state: FSMContext):
    text = message.text
    ind = text.find(',', 1)
    user_id = text[1:ind]
    if text.lower() == '<-back':
        await bot.admin_menu(message)
        await state.finish()
        return
    try:
        for row in user_db.sql_show_users():
            if row[0] == int(user_id):
                user_db.sql_delete_user(user_id)
                await message.answer(f'User {user_id} removed')
                await bot.admin_menu(message)
                await state.finish()
    except Exception:
        await message.reply('Error! User is not removed')


async def send_message_to_chat(message: types.Message, state: FSMContext):
    timeout = 30
    request = telegram.utils.request.Request(read_timeout=timeout)
    telegram_bot = telegram.Bot(token, request=request)
    parse_mode = None
    silent = False
    disable_web_page_preview = False

    info_message = f"⚡️⚡️⚡️\n️Сообщение от администратора:\n{message.text}\n⚡️⚡️⚡️"
    chats = url_db.sql_all_status()

    for chat_id in chats:
        telegram_bot.send_message(
            chat_id=chat_id[0], text=info_message, parse_mode=parse_mode, disable_notification=silent,
            disable_web_page_preview=disable_web_page_preview
        )
    await bot.admin_menu(message)
    await state.finish()
