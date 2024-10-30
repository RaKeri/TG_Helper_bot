import asyncio
import ctypes
import datetime
import glob
import multiprocessing
import os
import random
import re
import sys
import time
import json
from collections import Counter
from logging.handlers import TimedRotatingFileHandler
from multiprocessing import Process
from sqlite3 import OperationalError
import logging

import phonenumbers
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InputMediaPhoto, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient, errors

from clientWork.telethonWorker import startGrab
from tools.checkActivate import check_license, get_device_id, checkUpdate
from tools.createQR import generate_qr_code
from tools.fsm import Grab, Auth
from tools.keyboard import profile_keyboard, start_keyboard, generate_how_to_use_keyboard, answers_keyboard, \
    all_accounts_keyboard, check_logs_keyboard, check_parsing_keyboard, start_add_account_keyboard
from tools.uuidGen import UUID
from tools.checkProxy import ProxyChecker
from tools.posecc import check_string, is_digits
import flag

from db.database import DatabaseManager
from dotenv import load_dotenv
load_dotenv()

pathdir = os.path.dirname(os.path.abspath(__file__)) + "\\"

bot = Bot(token=os.getenv("BOT_TOKEN"), parse_mode="HTML")


api_id = 21628682
api_hash = "26c7cd0800b6449c4f9bbd29d1c81f7b"
Client_verison = "0.0.1"

dp = Dispatcher()
uuid_generator = UUID()
db = DatabaseManager()

"""Запускаме логирование"""


log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

FILE_ATTRIBUTE_HIDDEN = 0x02
ctypes.windll.kernel32.SetFileAttributesW(log_dir, FILE_ATTRIBUTE_HIDDEN)

# Логгер
logger = logging.getLogger("my_logger")
logger.setLevel(logging.DEBUG)

# Обработчик для логов за всё время
all_time_handler = logging.FileHandler(os.path.join(log_dir, "all_time.log"), encoding="UTF-8")
all_time_handler.setLevel(logging.DEBUG)
all_time_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
all_time_handler.setFormatter(all_time_format)

# Обработчик для логов за текущий день
daily_handler = TimedRotatingFileHandler(
    os.path.join(log_dir, "daily.log"),
    encoding="UTF-8",
    when="midnight",  # Смена файла в полночь
    interval=1,
    backupCount=30  # Храним логи за последние 7 дней
)
daily_handler.setLevel(logging.DEBUG)
daily_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
daily_handler.setFormatter(daily_format)

# Добавляем обработчики к логгеру
logger.addHandler(all_time_handler)
logger.addHandler(daily_handler)



"""---------------------------------------------------------"""


@dp.my_chat_member()
async def chat_member(message: types.Message):
    user_id = message.from_user.id
    if (message.old_chat_member.status == ChatMemberStatus.KICKED and
        message.new_chat_member.status == ChatMemberStatus.MEMBER):
        db.update_user_status(user_id, 0)
    elif (message.new_chat_member.status == ChatMemberStatus.KICKED and
          message.old_chat_member.status == ChatMemberStatus.MEMBER):
        db.update_user_status(user_id, 1)

@dp.callback_query(F.data.split("_")[0] == "dont")
async def dont(callback: types.CallbackQuery):
    await callback.answer("Данная функция пока не работает", show_alert=True)
    pass


@dp.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):

    user = db.fetch_user(message.from_user.id)

    if user is None:
        # Добавляем нового пользователя в базу данных
        db.add_user((message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name,
            time.time(), 0, 0, 0))

        await message.answer(
            f"Добро пожаловать в бота {message.from_user.first_name} ознакомься с правилами прежде чем приступить к работе.",
            reply_markup=start_keyboard())
    else:
        await message.answer(f"Добро пожаловать {message.from_user.first_name}",
                             reply_markup=start_keyboard())


def get_active_processes():
    active = multiprocessing.active_children()
    if active:
        header = "\n\n<b>В работе</b>:\n┏━━━━━━━━━━━┓"
        footer = "┗━━━━━━━━━━━┛"
        process_list = "\n".join("• " + str(p.name) for p in active)
        return f"{header}\n{process_list}\n{footer}"
    else:
        return ""



@dp.callback_query(F.data == "profile")
async def profile(callback: types.CallbackQuery):
    await callback.answer()
    user = db.fetch_user(callback.from_user.id)
    device_id = get_device_id()
    lic = check_license(device_id)
    data = datetime.datetime.fromtimestamp(int(lic))
    await callback.message.edit_text(f'''🤖 Профиль
➖➖➖➖➖➖➖➖➖➖
🆔 <b>ID</b>: <code>{user[0]}</code>
🔢 <b>Аккаунтов</b>: <code>{user[5]}</code>
📆 <b>Лицензия до</b>: <code>{data.date()}</code>{get_active_processes()}
''', reply_markup=profile_keyboard())




@dp.callback_query(F.data.split("_")[0] == "answers")
async def answers(callback: types.CallbackQuery):


    try:
        await callback.message.edit_text("Вопрос -- ответ:\n➖➖➖➖➖➖➖➖➖➖", reply_markup=answers_keyboard())
    except Exception as e:

        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")
        await callback.message.answer("Вопрос -- ответ:\n➖➖➖➖➖➖➖➖➖➖", reply_markup=answers_keyboard())

@dp.callback_query(F.data.split("_")[0] == "howToUse")
async def how_to_use(callback: types.CallbackQuery):
    step = int(callback.data.split("_")[1])

    photos = [
        # ("AgACAgIAAxkBAANcZaQCJVK41uVSMR2Wa4aEudiV2a8AAkrTMRuAmiBJ0hWrCmcm_0MBAAMCAAN4AAM0BA",
        #  "<b>1.</b> После регистрации вам будет доступна <b>пробная</b> подписка на <i><u>2 часа</u></i> подключить ее можно в разделе <b>\"ПОДПИСКА -> FREE\"</b>"),

        ("AgACAgIAAxkBAANdZaQCKdK5Jw3RqWoT7tIeEEh7LOkAAkvTMRuAmiBJ1LABt0H295kBAAMCAAN4AAM0BA",
         "<b>1.</b> Требуется добавить аккаунт с которого будете вести каналы, для этого нужно выполнить 5 простых действий"),

        ("AgACAgIAAxkBAANeZaQCLmd9hbjto-HdfrQiTUgquGIAAkzTMRuAmiBJowYBmVR9MIUBAAMCAAN4AAM0BA",
         "<b>2.</b> В итоге вам будет доступно меню управления аккаунтом."),

        ("AgACAgIAAxkBAANfZaQCNUiKyYY3a9fMv8TTfeTIpisAAk3TMRuAmiBJZwQyWQABqS-aAQADAgADeAADNAQ",
         "<b>3.</b> В Пункте 1 и 3 вам будет доступна настройка фильтров, а также нескольких параллельных задач.")
    ]

    keyboard = generate_how_to_use_keyboard(step)

    if step == 0:
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")
        await callback.message.answer_photo(
            photo=photos[step][0],
            caption=photos[step][1],
            reply_markup=keyboard
        )
    else:
        media = InputMediaPhoto(media=photos[step][0], caption=photos[step][1])
        await callback.message.edit_media(media=media, reply_markup=keyboard)




@dp.callback_query(F.data.split("_")[0] == "account")
async def acc6(callback: types.callback_query, id = None):
    accs = db.fetch_accounts(callback.from_user.id)

    try:
        await callback.message.edit_text("Ваши аккаунты:\n➖➖➖➖➖➖➖➖➖➖", reply_markup=all_accounts_keyboard(accs))
    except Exception as e:
        if id:
            await bot.edit_message_text(message_id=id, chat_id=callback.from_user.id, text="Ваши аккаунты:\n➖➖➖➖➖➖➖➖➖➖", reply_markup=all_accounts_keyboard(accs))
        else:
            await callback.answer("Ваши аккаунты:\n➖➖➖➖➖➖➖➖➖➖", reply_markup=all_accounts_keyboard(accs))


@dp.callback_query(F.data.split("_")[0] == "quit")
async def quit(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()

    ccs = db.accounts_from_phone(callback.data.split('_')[1])
    client = TelegramClient(f"{callback.data.split('_')[1]}.session", api_id, api_hash, device_model=ccs[13],
                            system_version=ccs[14], app_version=ccs[15])
    await client.connect()
    await client.log_out()
    await client.disconnect()
    db.del_to_db_account(callback.data.split('_')[1], callback.from_user.id)
    await callback.message.edit_text("Для того чтобы заново использовать данный аккаунт — авторизуйтесь")


@dp.callback_query(F.data.split("_")[0] == "Chaccount")
async def acc5(callback: types.CallbackQuery, state: FSMContext):

    a = db.accounts_from_phone(callback.data.split('_')[1])
    procCur = False
    for p in multiprocessing.active_children():
        if p.name == callback.data.split("_")[1]:
            procCur = True
            break
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="1", callback_data="ActionAccount_1_" + callback.data.split("_")[1]))
    builder.add(InlineKeyboardButton(text="2", callback_data="ActionAccount_2_" + callback.data.split("_")[1]))
    builder.add(InlineKeyboardButton(text="3", callback_data="ActionAccount_3_" + callback.data.split("_")[1]))
    builder.add(InlineKeyboardButton(text="4", callback_data="ActionAccount_4_" + callback.data.split("_")[1]))
    builder.add(InlineKeyboardButton(text="5", callback_data="dont_" + callback.data.split("_")[1]))
    builder.row(InlineKeyboardButton(text=("Добавить прокси" if a[12] == None else "Изменить прокси"),
                                     callback_data="addProxy_" + callback.data.split("_")[1]),
                InlineKeyboardButton(text="Завершить сессию", callback_data="quit_" + callback.data.split("_")[1]))
    builder.row(InlineKeyboardButton(text=f"Статус ({'🟢' if procCur == 'ACTIVE' else '🔴'})",
                                     callback_data="changeStatus_" + callback.data.split("_")[1] + "_" + (
                                         "DISABLE" if procCur == 'ACTIVE' else "ACTIVE")))
    # builder.row(InlineKeyboardButton(text="Скачать файл сессии", callback_data="downloadFileSession_" + callback.data.split("_")[1]))
    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data="account"))
    await state.update_data(chooseActionFrom=[])
    await state.update_data(chooseActionTo=[])
    await state.update_data(phone=callback.data.split("_")[1])

    await callback.message.edit_text(
        f"Аккаунт (<i>{callback.data.split('_')[1]}</i>|<b>@{a[2]}</b>)\n➖➖➖➖➖➖➖➖➖➖\n🆕1. Пересылать <i><b>новые</b></i> посты\n💾2. Парсинг пользователей\n📤3. Переслать <i><b>старые</b></i> сообщения\n📤4. Скачать все <i><b>медиафайлы и текстовый</b></i> сообщения\n🤖<tg-spoiler>5. Автопостинг с помощью ИИ (в разработке)</tg-spoiler>",
        reply_markup=builder.as_markup())

@dp.callback_query(F.data.split("_")[0] == "downloadFileSession")
async def downloadFileSession(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Ожидайте")
    session = FSInputFile(callback.data.split("_")[1] +".session")
    await callback.message.answer_document(
        session
    )

@dp.callback_query(F.data.split("_")[0] == "addProxy")
async def addProxy(callback: types.CallbackQuery, state: FSMContext):

    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + callback.data.split("_")[1]))
    s = await callback.message.edit_text(
        "Введите прокси в формате:\n<pre><code style=\"language-python\">http;127.0.0.1;5555;LOGIN;PASSWORD</code></pre>или\n<pre><code style=\"language-python\">http;127.0.0.1;5555</code></pre>\nПоддерживаемые протоколы: (http)",
         reply_markup=builder.as_markup())
    await state.update_data(messageId=s.message_id)
    await state.set_state(Grab.enter_Proxy)


@dp.message(Grab.enter_Proxy)
async def checkProxy(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if not "phone" in data:
        await acc6(message, data["messageId"])
        return
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + data["phone"]))
    if check_string(message.text.lower()):
        checker = ProxyChecker()
        s = await checker.check_proxy(message.text.lower())
        if not s:
            await message.answer("Введенные прокси не работают, попробуйте другие",
                                 reply_markup=builder.as_markup())
            return

        await state.clearState()
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")

        try:
            await bot.delete_message(chat_id=message.from_user.id, message_id=data["messageId"])
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")

        await message.answer(s,  reply_markup=builder.as_markup())
        await state.clearState()
        db.update_proxy(message.text.lower(), data["phone"])
        return
    else:
        await message.answer("Прокси введены некорректно, введите еще раз",
                             reply_markup=builder.as_markup())



def find_files(directory, id, phone):
    # Получаем список всех файлов с расширением .csv в указанной директории
    files = glob.glob(os.path.join(directory, '*.csv'))

    # Отфильтровываем файлы, имя которых начинается с указанного ID
    files = [f for f in files if os.path.basename(f).split("_")[0] == str(id) and os.path.basename(f).split("_")[1] == phone.replace("+", "")]

    # Сортируем файлы по времени создания (от самого нового к самому старому)
    files.sort(key=os.path.getctime, reverse=True)

    return files


@dp.callback_query(F.data.split("_")[0] == "checkParsing")
async def checkParsing(callback: types.CallbackQuery, state: FSMContext):
    files = find_files(pathdir + "parseData", callback.from_user.id, callback.data.split("_")[1])


    await callback.message.edit_text(
        "Скачать файлы парсинга можно ниже\n➖➖➖➖➖➖➖➖➖➖\n",
         reply_markup=check_parsing_keyboard(callback, files))


@dp.callback_query(F.data.split("_")[0] == "downloadPars")
async def downloadPars(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    document = types.FSInputFile(
        pathdir.replace("/", "\\") + "parseData\\" + callback.data.split("_")[2] + "_" + callback.data.split("_")[
            3] + "_" + callback.data.split("_")[4] + ".csv")
    await bot.send_document(callback.from_user.id, document=document)
    await checkParsing(callback, state)


@dp.callback_query(F.data.split("_")[0] == "changeStatus")
async def changeStatus(callback: types.CallbackQuery, state: FSMContext):
    db.update_account_status(callback.data.split("_")[2], (time.time() if callback.data.split("_")[2] == "ACTIVE" else None), callback.data.split("_")[1])
    phone = callback.data.split("_")[1]
    if not any(p.name == str(phone) for p in multiprocessing.active_children()):
        p = Process(target=startGrab, args=(phone,), name=str(phone))
        p.start()
        await callback.answer(f"Запущен аккаунт {p.name}", show_alert=True)
    else:
        for p in multiprocessing.active_children():
            if p.name == phone:
                p.terminate()
                await callback.answer(f"Остановлен аккаунт {p.name}", show_alert=True)
                break
    await acc5(callback, state)


@dp.callback_query(F.data.split("_")[0] == "ActionAccount")
async def acc4(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + callback.data.split('_')[2]))
    data = await state.get_data()
    if not "chooseActionFrom" in data:
        await state.update_data(chooseActionFrom=[])
        await state.update_data(chooseActionTo=[])

    try:

        ccs = db.accounts_from_phone(callback.data.split('_')[2])

        client = TelegramClient(f"{callback.data.split('_')[2]}.session", api_id, api_hash, device_model=ccs[13],
                                system_version=ccs[14], app_version=ccs[15])
        await client.connect()
    except OperationalError as e:
        if e.sqlite_errorname == "SQLITE_BUSY":
            await callback.answer("Для редактирования статус должен быть — 🔴", show_alert=True)
        return
    s = ""
    chats = []
    flag = True
    i = 0
    async for chat in client.iter_dialogs(archived=False):
        if int(callback.data.split("_")[1]) == 2:
            if chat.is_group:
                chats.append(chat)
                if flag:
                    s += str(i) + ". " + chat.title + "\n"
                    flag = False
                else:
                    s += "<b>" + str(i) + ". " + chat.title + "</b>\n"
                    flag = True
                i += 1
        else:
            chats.append(chat)
            if flag:
                s += str(i) + ". " + chat.title + "\n"
                flag = False
            else:
                s += "<b>" + str(i) + ". " + chat.title + "</b>\n"
                flag = True
            i += 1
    await client.disconnect()
    await state.update_data(chats=chats)
    await state.update_data(phone=callback.data.split("_")[2])
    await state.update_data(action=callback.data.split("_")[1])
    await state.set_state(Grab.enter_id)
    if int(callback.data.split("_")[1]) in range(2, 5):
        ms = await callback.message.edit_text(
            "Выберите один канал/чат/группу, введите ID\n➖➖➖➖➖➖➖➖➖➖\n\n" + s,
             reply_markup=builder.as_markup())
    else:
        ms = await callback.message.edit_text(
            "Выберите <b>ИЗ</b> како(го|их) канала/чата/группы, введите ID через пробел например (1 3 10 101)\n➖➖➖➖➖➖➖➖➖➖\n\n" + s,
             reply_markup=builder.as_markup())
    await state.update_data(messageId=ms.message_id)


@dp.message(Grab.enter_id)
async def acc3(message: types.Message, state: FSMContext):
    match = re.match(r"^(\d+ ?)*$", message.text)
    data = await state.get_data()
    chats = data["chats"]

    if match:
        ids = [int(x) for x in message.text.split()]

        invalid = []
        for x in ids:
            if x < 0 or x > len(chats):
                invalid.append(x)

        if invalid:
            await message.answer(f"Я не знаю таких каналов с ID: {invalid}")
            return
    else:
        await message.answer("Ты ввел ID в неправильном формате")
        return
    await state.clearState()
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Ошибка при удалении сообщения: {e}")

    ss = data["chooseActionFrom"]
    ss.append(message.text)

    if int(data["action"]) == 2 or int(data["action"]) == 4:
        s = ""
        flag = True
        i = 1
        ids = [int(x) for x in message.text.split()]

        for id in ids:
            if flag:
                s += str(i) + ". " + chats[id].title + "\n"
                flag = False
            else:
                s += "<b>" + str(i) + ". " + chats[id].title + "</b>\n"
                flag = True
            i += 1
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="💨Начать", callback_data="start"))
        builder.row(types.InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + data["phone"]))
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["messageId"], text="┏━━━━━━━━━━━━━━━━━━━━┓\n" + s + "\n┗━━━━━━━━━━━━━━━━━━━━┛",
                             reply_markup=builder.as_markup())
        return

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + data["phone"]))
    s = ""
    flag = True
    i = 0
    for chat in chats:
        if flag:
            s += str(i) + ". " + chat.title + "\n"
            flag = False
        else:
            s += "<b>" + str(i) + ". " + chat.title + "</b>\n"
            flag = True
        i += 1

    await state.update_data(chooseActionFrom=ss)
    await state.clearState()
    await state.set_state(Grab.enter_idTO)
    await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["messageId"], text=
        "Выберите <b>В</b> как(ой|ие) канал/чат/группу, введите ID через пробел например (1 3 10 101)\n➖➖➖➖➖➖➖➖➖➖\n\n" + s,
         reply_markup=builder.as_markup())


@dp.message(Grab.enter_idTO)
async def acc2(message: types.Message, state: FSMContext):
    match = re.match(r"^(\d+ ?)*$", message.text)
    data = await state.get_data()
    chats = data["chats"]
    if match:
        ids = [int(x) for x in message.text.split()]

        invalid = []
        for x in ids:
            if x < 0 or x > len(chats):
                invalid.append(x)

        if invalid:
            await message.answer(f"Я не знаю таких каналов с ID: {invalid}")
            return
    else:
        await message.answer("Ты ввел ID в неправильном формате")
        return
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Ошибка при удалении сообщения: {e}")
    await state.clearState()
    if not "filters" in data:
        await state.update_data(filters=[])
        data = await state.get_data()
    filter = data["filters"]
    if len(filter) != len(data["chooseActionFrom"]):
        filter.append({
            "delURL": False,
            "delAllURL": False,
            "delTEXT": False,
            "translate": False,
            "addSourceChannel": False,
            "translateLang": "",
            "tag": "",
            "filters": [],
            "goodKeys": [],
            "badKeys": [],
            "transcribation": False
        })
        await state.update_data(filters=filter)
    ss = data["chooseActionTo"]
    ss.append(message.text)
    await state.update_data(chooseActionTo=ss)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💨Начать", callback_data="start"))
    builder.row(types.InlineKeyboardButton(text="Добавить фильтры",
                                           callback_data="AddFilter_" + data["action"] + "_" + data["phone"]))
    if not int(data["action"]) == 3:
        builder.row(types.InlineKeyboardButton(text="Добавить задачу",
                                               callback_data="ActionAccount_" + data["action"] + "_" + data["phone"]))
    builder.row(types.InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + data["phone"]))
    s = ""
    for ij in range(0, len(data["chooseActionFrom"])):

        sFrom = ""
        sTo = ""

        flag = True
        i = 1
        ids = [int(x) for x in data["chooseActionFrom"][ij].split()]

        for id in ids:
            if flag:
                sFrom += str(i) + ". " + chats[id].title + "\n"
                flag = False
            else:
                sFrom += "<b>" + str(i) + ". " + chats[id].title + "</b>\n"
                flag = True
            i += 1
        flag = True
        i = 1
        ids = [int(x) for x in data["chooseActionTo"][ij].split()]
        for id in ids:
            if flag:
                sTo += str(i) + ". " + chats[id].title + "\n"
                flag = False
            else:
                sTo += "<b>" + str(i) + ". " + chats[id].title + "</b>\n"
                flag = True
            i += 1
        s += "┏━━━━━━━━" + str(
            ij + 1) + " Задача━━━━━━━┓\nВсе сообщения из чата(ов): \n" + sFrom + "\nВ чат(ы):\n" + sTo + "┗━━━━━━━━━━━━━━━━━━━━┛\n\n"

    await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["messageId"], text=s,  reply_markup=builder.as_markup())


@dp.callback_query(F.data.split("_")[0] == "AddFilter")
async def acc1(callback: types.CallbackQuery, state: FSMContext):


    builder = InlineKeyboardBuilder()
    data = await state.get_data()
    if not "action" in data:
        await acc6(callback)
        return
    if not "filters" in data:
        await state.update_data(filters=[])
        data = await state.get_data()
    filter = data["filters"]

    if len(filter) != len(data["chooseActionFrom"]):
        filter.append({
            "delURL": False,
            "delAllURL": False,
            "delTEXT": False,
            "translate": False,
            "addSourceChannel": False,
            "translateLang": "",
            "tag": "",
            "filters": [],
            "goodKeys": [],
            "badKeys": [],
            "transcribation": False
        })
        await state.update_data(filters=filter)
    try:

        if callback.data.split("_")[1] is not None and callback.data.split("_")[1] != str(1) and \
                callback.data.split("_")[1] != str(2) and callback.data.split("_")[1] != str(3):
            filter_name = callback.data.split("_")[1]
            filter = data["filters"]
            filter[len(data["chooseActionFrom"]) - 1][filter_name] = not bool(
                data["filters"][(len(data["chooseActionFrom"]) - 1)][filter_name])
            if bool(filter[len(data["chooseActionFrom"]) - 1][filter_name]):
                match callback.data.split("_")[1]:
                    case "delURL":
                        await callback.answer(
                            "Ссылки которые помечены у нас как рекламные или нежелательные будут удалятся из поста.",
                            show_alert=True)
                    case "delAllURL":
                        await callback.answer("Все ссылки будут удалятся из поста.", show_alert=True)
                    case "delText":
                        await callback.answer("Весь текст сообщения будет удален.", show_alert=True)
                    case "transcribation":
                        await callback.answer("Вместе с ГС и кружками будет отправятся текстовая расшифровка.",
                                              show_alert=True)
                    case "addSourceChannel":
                        await callback.answer("Добавляет в конец поста ссылку на ИСХОДНЫЙ канал поста.",
                                               show_alert=True)
            await state.update_data(filters=filter)

    except Exception as e:
        pass

    data = await state.get_data()

    filter_options = [
        ("delURL", "🗑 Рекл. ссылки"),
        ("delAllURL", "🗑 Все ссылки"),
        ("delTEXT", "🗑 Текст"),
        #("transcribation", "Транскрибация"),
        ("addSourceChannel", "Доб. назв. исх. канала")
    ]

    for option in filter_options:
        filter_name, filter_text = option

        selected = "✅" if data["filters"][(len(data["chooseActionFrom"]) - 1)][filter_name] else "❌"
        button_text = f"{selected} {filter_text}"
        callback_data = f"AddFilter_{filter_name}"

        builder.add(InlineKeyboardButton(text=button_text, callback_data=callback_data))

    builder.adjust(2)

    selected = "✅" if data["filters"][(len(data["chooseActionFrom"]) - 1)]["translate"] else "❌"
    builder.row(InlineKeyboardButton(text=selected + " Перевод ->", callback_data="AddFilter_translate"),
                InlineKeyboardButton(text="Выберите язык" if data["filters"][(len(data["chooseActionFrom"]) - 1)][
                                                                 "translateLang"] == "" else f'Язык ({data["filters"][(len(data["chooseActionFrom"]) - 1)]["translateLang"]})',
                                     callback_data="set_translateLang"))

    builder.row(InlineKeyboardButton(text="Тег", callback_data=f"set_tag"),InlineKeyboardButton(text="Медиа-фильтры", callback_data=f"set_filters"))
    builder.row(InlineKeyboardButton(text="Слова-ключ.", callback_data=f"set_goodKeys"),InlineKeyboardButton(text="Слова-исключ.", callback_data=f"set_badKeys"))


    if not int(data["action"]) == 3:
        builder.row(InlineKeyboardButton(text="Добавить задачу",
                                         callback_data="ActionAccount_" + data["action"] + "_" + data["phone"]))
    builder.row(InlineKeyboardButton(text="💨Начать", callback_data="start"),
                InlineKeyboardButton(text="🔙Назад", callback_data=f"Chaccount_{data['phone']}"))
    try:
        await callback.message.edit_text("Фильтры", reply_markup=builder.as_markup())
    except Exception as e:
        await callback.answer("Фильтры", reply_markup=builder.as_markup())


@dp.callback_query(F.data.split("_")[0] == "set")
async def acc7(callback: types.callback_query, state: FSMContext):


    data = await state.get_data()
    if not "filters" in data and not "action" in data:
        await acc6(callback)
        return
    await state.update_data(condition=callback.data.split("_")[1])
    await state.set_state(Grab.waitFilter)

    match callback.data.split("_")[1]:
        case "tag":

            await callback.message.edit_text("Введите тег для использование в данной задаче. Он будет вставляться в конце поста.")
        case "filters":
            await callback.message.edit_text("""Введите фильтры через пробел для использование в данной задаче\n
0 - все сообщения (за исключением пересланных сообщений)  ВНИМАНИЕ: <i><u>используется отдельно от других фильтров;</u></i>
<b>1 - все сообщения  ВНИМАНИЕ: <u><i>используется отдельно от других фильтров;</i></u></b>\n
ФИЛЬТРЫ НИЖЕ МОЖНО СОВМЕЩАТЬ\n
<b>2 - сообщения с фото;</b>
3 - сообщения с видео;
<b>4 - сообщения с документом;</b>
5 - текстовые сообщения;
<b>6 - сообщения содержащее какую либо ссылку;</b>
7 - Видеосообщения;
<b>8 - Голосовые сообщения;</b>""")
        case "translateLang":
            await callback.message.edit_text("Введите язык в формате ISO 639-1 например (en, ru, fr) для  использование в данной задаче.")
        case "goodKeys":
            await callback.message.edit_text(
                "Введите ключевые слова через пробел. Сообщения с этими словами будут пересылаться")
        case "badKeys":
            await callback.message.edit_text(
                "Введите слова исключения через пробел. Сообщения с этими словами будут игнорироваться")


@dp.message(Grab.waitFilter)
async def acc8(message: types.Message, state: FSMContext):

    data = await state.get_data()
    if not "filters" in data and not "action" in data:
        await message.answer(
            "Начните весь процесс заново, во время настройки не отвлекайтесь на другие пункты меню нашего бота.")
        return
    filter = data["filters"]
    filter[len(data["chooseActionFrom"]) - 1][data["condition"]] = message.text
    await state.update_data(filters=filter)
    await acc1(message, state)


@dp.callback_query(F.data.split("_")[0] == "start")
async def start(callback: types.CallbackQuery, state: FSMContext):


    data = await state.get_data()
    if not "filters" in data and not "action" in data:
        await acc6(callback)
        return
    if not "filters" in data:
        await state.update_data(filters=[])
    data = await state.get_data()
    chats = []
    for ig in data["chats"]:
        chats.append({
            "title": ig.title,
            "id": ig.id
        })

    db.start_accounts(time.time(), json.dumps(chats), "ACTIVE", json.dumps(data["chooseActionFrom"]), json.dumps(data["chooseActionTo"]), json.dumps(data["filters"]), data["action"], data["phone"])

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data=f"Chaccount_{data['phone']}"))
    if int(data["action"]) in [1, 3]:
        await callback.message.edit_text(
            "Процесс скоро будет запущен, отслеживать <u>логи</u> вы можете в меню данного аккаунта",
            reply_markup=builder.as_markup())
    if int(data["action"]) == 2:
        await callback.message.edit_text(
            "Процесс скоро будет запущен, результаты парсинга вы можете найти по пути \"Логи -> Парсинг\"",

            reply_markup=builder.as_markup())
    if int(data["action"]) == 4:
        await callback.message.delete()
    aa = data["phone"]
    p = Process(target=startGrab, args=(aa,), name=str(data['phone']))
    p.start()


# Auth new account-------------------------------------------------------------------------------------------------

@dp.callback_query(F.data.split("_")[0] == "accountAdd")
async def accs(callback: types.CallbackQuery, state: FSMContext):


    await callback.message.edit_text("Введите номер телефона в международном формате, например (+1234567890): \n<tg-spoiler>Так-же вы можете прислать нам файл <i><b>.session</b></i> (авторизованный через <u><b>telethon</b></u>) либо напишите 1 - для авторизации по QR-code.</tg-spoiler>", reply_markup=start_add_account_keyboard())
    await state.set_state(Auth.enter_phone)
    await state.update_data(mid=callback.message.message_id)


@dp.message(Auth.enter_phone, F.document)
async def enter_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if message.document.file_name.split(".")[-1] != "session":
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["mid"],
                                    text="Файл сессии должен быть с расширением \"*.session\"",
                                    reply_markup=start_add_account_keyboard())
        return

    await bot.download(
        message.document,
        destination=f"{pathdir}/{message.document.file_name}"
    )
    client = TelegramClient(message.document.file_name, api_id, api_hash)
    await client.connect()
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Ошибка при удалении сообщения: {e}")
    if not await client.is_user_authorized():
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["mid"],
                                    text="Сессия не активна",
                                    reply_markup=start_add_account_keyboard())
        await client.log_out()
        return
    me = await client.get_me()
    await client.disconnect()


    dm = 'GRBS ' + str(random.randint(0, 20)) + "." + str(random.randint(0, 20)) + "." + str(random.randint(0, 20))
    sv = 'telegram ' + str(random.randint(0, 20)) + "." + str(random.randint(0, 20)) + "." + str(
        random.randint(0, 20))
    av = '' + str(random.randint(0, 20)) + "." + str(random.randint(0, 20)) + "." + str(random.randint(0, 100))

    db.add_to_db_account(message.document.file_name.split(".")[0], message.from_user.id, me.username, me.first_name, dm, sv, av)
    await acc6(message, data["mid"])


@dp.message(Auth.enter_phone, F.text != "1")
async def enter_phone(message: types.Message, state: FSMContext):
    phone = message.text
    data = await state.get_data()
    number = phonenumbers.parse(phone)

    if phonenumbers.is_valid_number(number):
        country_code = phonenumbers.region_code_for_country_code(number.country_code)
        fl = flag.flag(country_code)
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["mid"], text=f"Код подтверждения был отправлен на номер ({fl}<i><b>{phone}</b></i>), введите его: ",
                             reply_markup=start_add_account_keyboard())
        dm = 'GRBS ' + str(random.randint(0, 20)) + "." + str(random.randint(0, 20)) + "." + str(random.randint(0, 20))
        sv = 'telegram ' + str(random.randint(0, 20)) + "." + str(random.randint(0, 20)) + "." + str(
            random.randint(0, 20))
        av = '' + str(random.randint(0, 20)) + "." + str(random.randint(0, 20)) + "." + str(random.randint(0, 100))
        await state.update_data(deviceModel=dm)
        await state.update_data(systemVersion=sv)
        await state.update_data(appVersion=av)

        client = TelegramClient(phone, api_id, api_hash, device_model=dm, system_version=sv, app_version=av)
        await client.connect()
        try:
            await client.send_code_request(phone)
        except Exception as e:
            await client.connect()
            await client.send_code_request(phone)
        await state.update_data(client=client)
        await state.update_data(phone=phone)
        await state.set_state(Auth.enter_code)
    else:
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=data["mid"], text="Введенный номер телефона недействителен.", reply_markup=start_add_account_keyboard())
        await state.set_state(Auth.enter_phone)


@dp.message(Auth.enter_phone, F.text == "1")
async def enter_phone(message: types.Message, state: FSMContext):
    # Генерация случайных данных для устройства и версий
    dm = f'GRBS {random.randint(0, 20)}.{random.randint(0, 20)}.{random.randint(0, 20)}'
    sv = f'telegram {random.randint(0, 20)}.{random.randint(0, 20)}.{random.randint(0, 20)}'
    av = f'{random.randint(0, 20)}.{random.randint(0, 20)}.{random.randint(0, 100)}'

    await state.update_data(deviceModel=dm, systemVersion=sv, appVersion=av)

    if os.path.exists("old_session_file"):
        os.remove("sessionQR.session")

    # Инициализация клиента Telegram
    client = TelegramClient("sessionQR", api_id, api_hash,
                            device_model=dm, system_version=sv, app_version=av)
    await client.connect()

    qr_login = await client.qr_login()
    await message.delete()

    state_data = await state.get_data()
    await bot.delete_message(message_id=state_data.get("mid"), chat_id=message.chat.id)

    # Ожидание авторизации через QR-код
    authorized = await wait_for_authorization(client, qr_login, bot, message, state)

    if authorized:
        user = await client.get_me()
        phone_number = user.phone

        # Закрытие клиента и переименование сессионного файла
        await client.disconnect()
        old_session_file = "sessionQR.session"
        new_session_file = f"+{phone_number}.session"

        if os.path.exists(old_session_file):
            try:
                os.rename(old_session_file, new_session_file)
            except PermissionError:
                time.sleep(2)  # Повторить попытку при блокировке файла
        state_data = await state.get_data()
        await bot.delete_message(chat_id=message.chat.id, message_id=state_data.get("messs"))
        mid = await bot.send_message(
            chat_id=message.from_user.id,
            text="Авторизация прошла успешно. Вы можете настроить бота.",
        )
        await state.clear()
        # Сохранение данных в БД (пример)
        db.add_to_db_account(
            "+" + str(phone_number), message.from_user.id,
            user.username, user.first_name, dm, sv, av
        )
        await acc6(message, mid.message_id)
    else:
        await client.disconnect()
        await bot.send_message(
            chat_id=message.chat.id,
            text="Введите номер телефона в международном формате или используйте QR-код.",
            reply_markup=start_add_account_keyboard(),
        )
        await state.set_state(Auth.enter_phone)

async def wait_for_authorization(client, qr_login, bot, message, state):
    """Ожидает авторизацию пользователя через QR-код."""
    start_time = time.time()
    authorized = False

    while not authorized:
        if time.time() - start_time > 60:
            break  # Прерываем ожидание через 60 секунд

        qr_code_file = generate_qr_code(qr_login.url)
        state_data = await state.get_data()

        if state_data.get("messs", 0):
            if state_data.get("qr_url") != qr_login.url:
                media = InputMediaPhoto(media=qr_code_file, caption="Отсканируйте QR-код.")
                await bot.edit_message_media(
                    chat_id=message.chat.id,
                    message_id=state_data.get("messs"),
                    media=media,
                )
                await state.update_data(qr_url=qr_login.url)
        else:
            sent_message = await bot.send_photo(
                chat_id=message.chat.id,
                photo=qr_code_file,
                caption="Отсканируйте QR-код."
            )
            await state.update_data(messs=sent_message.message_id, qr_url=qr_login.url)

        try:
            authorized = await qr_login.wait()
        except errors.SessionPasswordNeededError:
            return False  # Авторизация потребовала пароль
        except Exception:
            await qr_login.recreate()  # Пересоздать QR-код при ошибке

    return authorized



@dp.message(Auth.enter_code)
async def enter_code(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    code = re.findall(r'\d+', message.text)
    code = ''.join(code)
    if is_digits(code):
        client = user_data["client"]
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Ошибка при удалении сообщения: {e}")
        try:
            await client.sign_in(phone=user_data["phone"], code=code)
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=user_data["mid"], text="Авторизация прошла успешно, через пару секунд вы сможете настроить работу бота")
            me = await client.get_me()
            await client.disconnect()
            await state.clear()
            db.add_to_db_account(user_data["phone"], message.from_user.id, me.username, me.first_name,
                              user_data["deviceModel"], user_data["systemVersion"], user_data["appVersion"])
            await acc6(message, user_data["mid"])
        except errors.SessionPasswordNeededError:
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=user_data["mid"], text="Ваш аккаунт защищен паролем, введите его: ")
            await state.update_data(code=code)
            await state.update_data(client=client)
            await state.set_state(Auth.enter_password)
        except Exception as e:
            logger.warning(f"Ошибка при входе в аккаунт: {e}")
            await bot.edit_message_text(chat_id=message.from_user.id, message_id=user_data["mid"], text="Неверный код, попробуйте еще раз: ")
            await state.update_data(client=client)
            await state.set_state(Auth.enter_code)
    else:
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=user_data["mid"], text="Код подтверждения должен состоять только из цифр.", reply_markup=start_add_account_keyboard())
        await state.set_state(Auth.enter_code)


@dp.message(Auth.enter_password)
async def enter_password(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    password = message.text
    client = user_data["client"]
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Ошибка при удалении сообщения: {e}")
    try:
        await client.sign_in(password=password)
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=user_data["mid"], text="Авторизация прошла успешно, через пару секунд вы сможете настроить работу бота")
        me = await client.get_me()
        await client.disconnect()
        await state.clear()
        db.add_to_db_account(user_data["phone"], message.from_user.id, me.username, me.first_name,
                          user_data["deviceModel"], user_data["systemVersion"], user_data["appVersion"])
        await acc6(message, user_data["mid"])
    except Exception as e:
        logger.warning(f"Ошибка при входе в аккаунт: {e}")
        await bot.edit_message_text(chat_id=message.from_user.id, message_id=user_data["mid"], text="Ваш аккаунт защищен паролем, введите его: ")
        await state.update_data(client=client)
        await state.set_state(Auth.enter_password)


def format_time_difference(time_difference):
    seconds = int(round(time_difference))

    if seconds < 60:
        return f"{seconds}с"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes}м {seconds}с"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds %= 60
        return f"{hours}ч {minutes}м {seconds}с"
    elif seconds < 2592000:  # Примерное количество секунд в месяце
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds %= 60
        return f"{days}д {hours}ч {minutes}м {seconds}с"
    else:
        months = seconds // 2592000
        days = (seconds % 2592000) // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        seconds %= 60
        return f"{months}м {days}д {hours}ч {minutes}м {seconds}с"


async def checkSubs():
    while True:
        device_id = get_device_id()
        if not check_license(device_id):
            await bot.send_message(chat_id=os.getenv("ME_ID"), text="Работа софта завершена, лицензия истекла")
            for p in multiprocessing.active_children():
                p.terminate()
            sys.exit(0)
        await asyncio.sleep(3600)  # Проверка каждый час и при запуске

async def checkU():
    while True:
        if os.access("./update.rar", os.F_OK):
            return
        ch = checkUpdate(Client_verison)
        if ch:
            try:
                await bot.send_message(chat_id=os.getenv("ME_ID"), text="‼️<b><u>Скачано новое обновление</u></b>‼️\nСкопируйте файлы из архива \"<code>update.rar</code>\" в текущую папку с <b>заменой</b>.\n<tg-spoiler>После чего выполните перезапуск программы и удалите архив, для возможности дальнейших обновлений</tg-spoiler>")
                return
            except Exception as e:
                logger.error(e)
                pass
        else:
            await asyncio.sleep(86400)  # Проверка каждый день и при запуске в случае если обновление не найдено

async def main():

    asyncio.create_task(checkSubs())
    asyncio.create_task(checkU())
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        device_id = get_device_id()
        if check_license(device_id):
            asyncio.run(main())
    except KeyboardInterrupt as e:
        print("Бот завершен")


