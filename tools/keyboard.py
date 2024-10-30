import datetime
import os

from aiogram import types
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🤖Профиль",
        callback_data="profile")
    )

    return builder.as_markup()


def profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🔵Аккаунты",
        callback_data="account")
    )
    builder.row(InlineKeyboardButton(
        text="❓️Вопросы",
        callback_data="answers")
    )
    return builder.as_markup()


def answers_keyboard():
    builder = InlineKeyboardBuilder()

    builder.add(types.InlineKeyboardButton(
        text="Как пользоваться?",
        callback_data="howToUse_0")
    )
    builder.add(types.InlineKeyboardButton(
        text="🔙Назад",
        callback_data="profile")
    )
    builder.adjust(1)
    return builder.as_markup()


def all_accounts_keyboard(accs):
    builder = InlineKeyboardBuilder()

    builder.add(types.InlineKeyboardButton(
        text="➕Добавить аккаунт",
        callback_data="accountAdd")
    )
    for a in accs:
        builder.add(types.InlineKeyboardButton(
            text=str(a[3]) + "|" + str(a[2]),
            callback_data="Chaccount_" + a[3])
        )

    builder.add(types.InlineKeyboardButton(
        text="🤖Профиль",
        callback_data="profile")
    )
    builder.adjust(2)
    return builder.as_markup()

def check_logs_keyboard(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Очистить логи", callback_data="clearLogs_" + callback.data.split("_")[1]))
    builder.add(InlineKeyboardButton(text="Парсинг", callback_data="checkParsing_" + callback.data.split("_")[1]))
    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data="Chaccount_" + callback.data.split("_")[1]))

    return builder.as_markup()

def check_parsing_keyboard(callback: types.CallbackQuery, files):
    builder = InlineKeyboardBuilder()

    for i, file in enumerate(files):
        data = datetime.datetime.fromtimestamp(os.path.getctime(file))
        strs = (file.split("\\")[-1]).split(".")[0]
        builder.add(InlineKeyboardButton(text=str(i) + f". " + str(data.date()),
                                         callback_data="downloadPars_" + callback.data.split("_")[1] + "_" + str(strs)))
    builder.adjust(2)

    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data="checkLogs_" + callback.data.split("_")[1]))

    return builder.as_markup()

def start_add_account_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙Назад", callback_data="account"))
    return builder.as_markup()



def generate_how_to_use_keyboard(step: int):
    builder = InlineKeyboardBuilder()

    if step > 0:
        builder.add(types.InlineKeyboardButton(text="<-", callback_data=f"howToUse_{step - 1}"))

    builder.add(types.InlineKeyboardButton(text="🔙Назад", callback_data="answers"))

    if step < 3:
        builder.add(types.InlineKeyboardButton(text="->", callback_data=f"howToUse_{step + 1}"))

    return builder.as_markup()