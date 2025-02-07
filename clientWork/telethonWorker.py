import asyncio
import csv
import glob
import json
import logging
import os
import random
import re
import shutil
import sqlite3
import sys
import time

from urllib.parse import urlparse
import mimetypes
import cv2
from mutagen import File

from telethon import TelegramClient, functions, errors, events, helpers, types, sync
from telethon.errors import FloodWaitError
from telethon.network import ConnectionTcpMTProxyRandomizedIntermediate
from telethon.types import MessageEntityUrl, MessageEntityTextUrl, MessageMediaWebPage
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeAudio, DocumentAttributeVideo, \
    MessageService, Message, MessageMediaPoll, DocumentAttributeSticker, MessageMediaGeo, MessageMediaVenue, \
    MessageMediaContact, Channel, Chat, InputPeerSelf

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from tools.translate import GoogleTranslator
from tools.Converter import Converter

from dotenv import load_dotenv
load_dotenv()

pathdir = os.path.dirname(os.path.abspath(__file__)).split("\\")[:-1]
pathdir = "\\".join(pathdir) + "\\"
api_id =  os.getenv("API_ID")
api_hash =  os.getenv("API_TOKEN")
timefreq = time.time()

translator = GoogleTranslator()
converter = Converter()

env_path = os.path.join(pathdir, ".env")

# Загружаем переменные окружения из .env
if os.path.exists(env_path):
    load_dotenv(env_path)

bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode='HTML'))
url_shorteners = []

logger = logging.getLogger("my_logger")


def startGrab(phone):
    try:
        Alldate = getAction(phone)
        if Alldate[12] is not None:
            pr = Alldate[12].split(";")
            if pr[0] == "mtproto":
                server = pr[1]
                port = pr[2]
                secret = pr[3]
                connection = ConnectionTcpMTProxyRandomizedIntermediate  # this mode supports most proxies
                client = TelegramClient(phone + ".session", api_id, api_hash, connection=connection,
                                        proxy=(server, port, secret), device_model=Alldate[13],
                                        system_version=Alldate[14], app_version=Alldate[15], sequential_updates=True)
            else:
                if len(pr) > 3:
                    prox = (pr[0], pr[1], int(pr[2]), True, pr[3], pr[4])
                else:
                    prox = (pr[0], pr[1], int(pr[2]), True)
                client = TelegramClient(phone + ".session", api_id, api_hash, proxy=prox, timeout=120,
                                        device_model=Alldate[13], system_version=Alldate[14], app_version=Alldate[15], sequential_updates=True)
                client.connect()
        else:
            client = TelegramClient(phone + ".session", api_id, api_hash, device_model=Alldate[13],
                                    system_version=Alldate[14], app_version=Alldate[15], sequential_updates=True)
            client.connect()
        match (Alldate[11]):
            case 1:
                Action1(phone, client, Alldate)
            case 2:
                loop = asyncio.get_event_loop()
                # Запуск корутины
                loop.run_until_complete(Action2(phone, client, Alldate))
            case 3:
                loop = asyncio.get_event_loop()
                # Запуск корутины
                loop.run_until_complete(Action3(phone, client, Alldate))
            case 4:
                loop = asyncio.get_event_loop()
                # Запуск корутины
                loop.run_until_complete(Action4(phone, client, Alldate))
    except FloodWaitError as e:
        time.sleep(e.seconds)
        print(e.seconds)
        startGrab(phone)
    except KeyboardInterrupt as e:
        print("terminate prosecc " + phone)



async def getTranscription(file):
#     connection = sqlite3.connect("database.db")
#     cursor = connection.cursor()
#     css = cursor.execute("SELECT * FROM keysEden").fetchone()
#     connection.commit()
#     connection.close()
#     edenai = EdenAI(css[2], css[1])
#     id = await edenai.speechToText(pathdir + file)
#     result = await edenai.getResultSTT(id)
    return ""


def delBadUrl(entities: list, text: str, raw_txt: int):
    if entities is not None:
        for t in reversed(entities):  # перебираем сущности в обратном порядке
            if isinstance(t, (MessageEntityTextUrl, MessageEntityUrl)):  # если сущность является URL
                url = t.url if isinstance(t, MessageEntityTextUrl) else raw_txt[t.offset:t.offset + t.length]
                domain = url.split('//')[-1].split('/')[0]
                if any(shortener in domain for shortener in url_shorteners):
                    # удаляем ссылку из текста
                    text = raw_txt[:t.offset] + raw_txt[t.offset + t.length:]


    # удаляем ссылки, заключенные в квадратные скобки
    text = re.sub(r'\[(.*?)\]\((.*?)\)(?:\s*[|\-\\/]\s*(.*))?', replace_ad_links, text)
    text = re.sub(r'http[s]?://\S+', replace_ad_links, text)
    # удаляем последнюю строку, если она содержит "http"
    lines = text.split("\n")
    if "http" in lines[-1]:
        text = '\n'.join(lines[:-1])
    return text


def delAllUrl(entities: list, text: str, raw_txt: int):
    if entities is not None:
        for t in reversed(entities):  # перебираем сущности в обратном порядке
            if isinstance(t, (MessageEntityTextUrl, MessageEntityUrl)):  # если сущность является URL
                text = raw_txt[:t.offset] + raw_txt[t.offset + t.length:]

        # удаляем ссылки, заключенные в квадратные скобки
    text = re.sub(r'\[(.*?)\]\((.*?)\)(?:\s*[|\-\\/]\s*(.*))?', text)
    text = re.sub('(?:https?|ftp):\/\/[^\s/$.?#].[^\s]*', text)

    # удаляем последнюю строку, если она содержит "http"
    lines = text.split("\n")
    if "http" in lines[-1]:
        text = '\n'.join(lines[:-1])
    return text


async def transcribStart(m, client: TelegramClient):
    if not hasattr(m, "media"):
        return
    if isinstance(m.media, MessageMediaDocument) and isinstance(
            m.media.document.attributes[0], DocumentAttributeVideo) and \
            m.media.document.attributes[0].round_message:
        if m.media.document.attributes[0].round_message:
            path = await client.download_media(m.media)

            try:
                os.remove(pathdir + path)
            except OSError as e:
                logger.error(e)
                pass
            return await getTranscription(path)
    if isinstance(m.media, MessageMediaDocument) and isinstance(
            m.media.document.attributes[0], DocumentAttributeAudio) and \
            m.media.document.attributes[0].voice:
        if m.media.document.attributes[0].voice:
            path1 = await client.download_media(m.media)
            path = await converter.ogg_to_mp3(path1)
            try:
                os.remove(pathdir + path1)
                os.remove(pathdir + path)
            except OSError as e:
                logger.error(e)
                pass
            return await getTranscription(path)
    return ""


async def addSourceChannel(currentId, text: str, AllData: list, client: TelegramClient):
    channel = await client.get_entity(currentId)
    channel_link = f'https://t.me/{channel.username}'
    if text == "":
        text = "Источник: [" + get_title_by_id(int(currentId),
                                               json.loads(AllData[7])) + "](" + channel_link + ")"
    else:
        text += "\n\nИсточник: [" + get_title_by_id(int(currentId), json.loads(AllData[7])) + "](" + channel_link + ")"
    return text


async def apply_message_filters(m, client, currentId, filter, AllData):
    """Применение фильтров к сообщению."""

    text, raw_txt = extract_message_data(m)

    if filter["delURL"]:
        text = delBadUrl(m.entities, text, raw_txt)

    if filter["delAllURL"]:
        text = delAllUrl(m.entities, text, raw_txt)

    if filter["delTEXT"]:
        text = ""

    if filter["transcribation"]:
        text = await transcribStart(m, client)

    if filter["addSourceChannel"]:
        text = await addSourceChannel(currentId, text, AllData, client)


    return helpers.del_surrogate(text) + filter["tag"]


########################################################################################


def Action1(phone: str, client: TelegramClient, AllData: list):
    chati = []
    for i, u in enumerate(json.loads(AllData[8])):
        for f in u.split():
            chati.append(json.loads(AllData[7])[int(f)]["id"])

    context = {"processed_groups": []}

    @client.on(events.NewMessage(chats=chati))
    async def Messages(event):
        try:
            processed_groups = context["processed_groups"]

            """Создаем переменные"""
            chatFromId, chatToId = [], []
            filter: list = json.loads(AllData[10])
            chatFrom: list = json.loads(AllData[8])
            chatTo: list = json.loads(AllData[9])
            zadacha = None
            currentId = (await event.get_sender()).id

            """Проверяем надо ли пересылать с данного канала"""
            for i, u in enumerate(chatFrom):
                for f in u.split():
                    if currentId == int(json.loads(AllData[7])[int(f)]["id"]) or int("-100" + str(currentId)) == int(
                            json.loads(AllData[7])[int(f)]["id"]):
                        zadacha = i
            """Если не найдено, то завершаем"""
            if zadacha == None:
                return
            if event.grouped_id and event.grouped_id in processed_groups:
                return

            """Получаем сообщения откуда и куда"""
            for ss in chatFrom[zadacha].split():
                chatFromId.append(json.loads(AllData[7])[int(ss)]["id"])
            for lk in chatTo[zadacha].split():
                chatToId.append(json.loads(AllData[7])[int(lk)]["id"])
            """Проверяем содержит ли текст BAD-слова"""
            if not event.raw_text == "":
                if [element for element in filter[zadacha]["badKeys"]
                    if event.raw_text.lower().__contains__(element)]:
                    return
            """Проверяем содержит ли текст GOOD-слова"""
            if len(filter[zadacha]["goodKeys"]) != 0:
                if not [element for element in filter[zadacha]["goodKeys"] if event.raw_text.lower().__contains__(element)]:
                    return
            """Удаляем медиа (ВЕБ-страницы и опросы)"""
            if isinstance(event.message.media, (MessageMediaWebPage, MessageMediaPoll)):
                event.message.media = None
            """Обрабатываем текст"""
            filtered_text = await apply_message_filters(event.message, client, currentId, filter[zadacha], AllData)
            filtered_text, formatting_entitiesd = await client._parse_message_text(message=filtered_text, parse_mode="md")
            fd = []
            if event.message.entities is None:
                fd = formatting_entitiesd
            else:
                fd = event.message.entities + formatting_entitiesd
            mes = filtered_text + filter[zadacha]["tag"]

            """Переводим текст"""
            if bool(filter[zadacha]["translate"]) and filter[zadacha]["translateLang"]:
                if mes != "":
                    mes = await translator.translate_text(mes, filter[zadacha]["translateLang"])
            """Получаем все сообщения связанные с этим"""
            media_group = [event.message]
            if event.grouped_id:
                media_group = await get_media_group(client, currentId, event.message.id)
            """Фильтруем сообщения"""
            try:
                flagFilter = False
                if len(filter[zadacha]["filters"]) == 0:
                    filter[zadacha]["filters"] = "0"
                for filt in filter[zadacha]["filters"].split():
                    for mg in media_group:
                        flagFilter = check_filter(mg, filt)
                        if flagFilter:
                            break
                if not flagFilter:
                    return
            except Exception as e:
                logger.error(("FlagFilter: ",e))
            """Отправляем сообщения"""
            folders = ""
            flag = 0
            chat = await event.get_sender()
            if isinstance(chat, Channel) or isinstance(chat, Chat) or isinstance(chat, Message):
                if chat.noforwards:
                    # Создаем папки для скачанных файлов
                    if not flag:
                        base_path = f"./downloads/channel_{currentId}"
                        folders = create_folder_structure(base_path)
                        flag = 1

                    # Проверяем, является ли сообщение частью медиагруппы
                    media = []
                    if event.grouped_id:
                        if event.grouped_id not in processed_groups:
                            processed_groups.append(event.grouped_id)

                            for mediaDownload in media_group:
                                media_path = await download_media(client, mediaDownload, folders)
                                if media_path is None:
                                    continue
                                with open(media_path, 'rb') as f:
                                    file = await client.upload_file(file=f)
                                media.append(await GETmedia_group(client, mediaDownload, file, media_path))


                            for ch in chatToId:
                                r = await client.send_file(entity=await client.get_entity(ch), file=media, formatting_entities=fd, caption=filtered_text)


                    if event.message.media is None:
                        for ch in chatToId:
                            r = await client.send_message(entity=await client.get_entity(ch), message=filtered_text, formatting_entities=fd)

                        return
                    media_path = await download_media(client, event.message, folders)
                    if media_path is None:
                        return
                    with open(media_path, 'rb') as f:
                        file = await client.upload_file(file=f)
                    media = await GETmedia_group(client, event.message, file, media_path)
                    for ch in chatToId:
                        r  = await client.send_file(entity=await client.get_entity(ch), file=media,
                                                               formatting_entities=fd, caption=filtered_text)
                    return
            media = []
            if event.grouped_id:
                if event.grouped_id not in processed_groups:
                    media_group = await get_media_group(client, currentId, event.message.id)

                    media.extend([me.media for me in media_group])
                    processed_groups.append(event.grouped_id)
            # Отправляем сообщение в целевые чаты
            for ch in chatToId:
                filters = filter[zadacha]["filters"] or "0"
                for filt in filters.split():

                    await send_forwarded_message(client, ch, filtered_text, event.message, media, filt)

        except Exception as e:
            logger.error(("GETnewMessage: ",e))
    client.run_until_disconnected()




########################################################################################


async def Action2(phone, client, AllData):
    all_participants = []

    for id in str(json.loads(AllData[8])[0]).split():
        async for user in client.iter_participants(json.loads(AllData[7])[int(id)]["id"]):
            all_participants.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone
            })
        time.sleep(5)

    with open(pathdir + "parseData/" + str(AllData[0]) + "_" + phone.replace("+", "") + '_' + str(
            random.randint(1, 10000000)) + '.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'username', 'first_name', 'last_name', 'phone'])
        writer.writeheader()
        writer.writerows(all_participants)
    await client.disconnect()
    sys.exit()
    pass


########################################################################################


def extract_message_data(m):
    """Извлечение данных из сообщения."""
    text = m.message or ""  # Если текста нет, устанавливаем пустую строку
    raw_txt = m.message or ""  # Аналогично для raw_txt

    # Проверяем, что текст не None, перед вызовом add_surrogate
    text = helpers.add_surrogate(text) if text else ""
    raw_txt = helpers.add_surrogate(raw_txt) if raw_txt else ""

    return text, raw_txt

async def send_forwarded_message(client, ch_id, mes, m, mediaG, filt):

    match int(filt):
        case 0:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: True)
        case 1:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: m.forward is not None)
        case 2:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: isinstance(media, MessageMediaPhoto))
        case 3:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: isinstance(media, MessageMediaDocument) and
                                    isinstance(media.document.attributes[0], DocumentAttributeVideo))
        case 4:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: isinstance(media, MessageMediaDocument) or
                                    (isinstance(media, MessageMediaDocument) and isinstance(
                                        media.document.attributes[0], DocumentAttributeAudio) and not media.document.attributes[0].voice))
        case 5:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: media is None)
        case 6:
            await process_text_FWmessage(client, ch_id, mes, m, mediaG, r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        case 7:
            s = await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: "round_video" if isinstance(media, MessageMediaDocument) and
                                        isinstance(media.document.attributes[0], DocumentAttributeVideo) and media.document.attributes[0].round_message else None)
            if s and mes:
                await send_FWTextmessage(client, ch_id, mes, m.entities)
        case 8:
            await process_FWmessage(client, ch_id, mes, m, mediaG, lambda media: "voice" if isinstance(media, MessageMediaDocument) and
                                    isinstance(media.document.attributes[0], DocumentAttributeAudio) and media.document.attributes[0].voice else None)

def check_filter(m, filt):
    match int(filt):
        case 0:
            return True
        case 1:
            return m.forward is not None
        case 2:
            return get_media_type(m.media) == "photo"
        case 3:
            return get_media_type(m.media) == "video"
        case 4:
            return get_media_type(m.media) == "document"
        case 5:
            return m.media is None
        case 6:
            return re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', m.text)
        case 7:
            return get_media_type(m.media) == "video_note"
        case 8:
            return get_media_type(m.media) == "voice"

async def Action3(phone, client, AllData):
    """Основная функция для обработки пересланных сообщений."""
    try:
        filter_data = json.loads(AllData[10])[0]
        chat_id = json.loads(AllData[7])[int(json.loads(AllData[8])[0])]["id"]
        processed_groups = []
        flag = 0
        folders = ""
        async for m in client.iter_messages(chat_id, reverse=True):
            try:
                # Проверяем, является ли сообщение корректным
                if isinstance(m, MessageService):
                    continue

                # Извлечение ID канала или пользователя
                currentId = (await m.get_sender()).id

                # Применяем фильтры к сообщению
                filtered_text = await apply_message_filters(m, client, currentId, filter_data, AllData)
                """Добавить получение кастомных ентити из текста"""
                filtered_text, formatting_entitiesd = await client._parse_message_text(message=filtered_text, parse_mode="md")

                fd = []
                if m.entities is None:
                    fd = formatting_entitiesd
                else:
                    fd = m.entities + formatting_entitiesd

                chat = await m.get_sender()
                if isinstance(chat, Channel) or isinstance(chat, Chat) or isinstance(chat, Message):
                    if chat.noforwards:
                        # Создаем папки для скачанных файлов
                        if not flag:
                            base_path = f"./downloads/channel_{currentId}"
                            folders = create_folder_structure(base_path)
                            flag = 1

                        # Проверяем, является ли сообщение частью медиагруппы
                        media = []
                        if m.grouped_id:
                            if m.grouped_id not in processed_groups:
                                media_group = await get_media_group(client, currentId, m.id)
                                processed_groups.append(m.grouped_id)
                                flagFilter = False

                                filters = filter_data["filters"] or "0"
                                for filt in filters.split():
                                    for mg in media_group:
                                        flagFilter = check_filter(mg, filt)
                                        if flagFilter:
                                            break
                                if not flagFilter:
                                    continue
                                filtered_text, formatting_entitiesd = await client._parse_message_text(
                                    message=filtered_text, parse_mode="md")
                                fd = []
                                if m.entities is None:
                                    fd = formatting_entitiesd
                                else:
                                    fd = m.entities + formatting_entitiesd
                                for mediaDownload in media_group:
                                    media_path = await download_media(client, mediaDownload, folders)
                                    if media_path is None:
                                        continue
                                    with open(media_path, 'rb') as f:
                                        file = await client.upload_file(file=f)
                                    media.append(await GETmedia_group(client, mediaDownload, file, media_path))

                                for ch in json.loads(AllData[9])[0].split(" "):
                                    ch_id = json.loads(AllData[7])[int(ch)]["id"]
                                    r = await client.send_file(entity=await client.get_entity(ch_id), file=media,
                                                               formatting_entities=fd, caption=filtered_text)

                        flagFilter = False

                        filters = filter_data["filters"] or "0"
                        for filt in filters.split():
                            flagFilter = check_filter(m, filt)
                            if flagFilter:
                                break

                        if not flagFilter:
                            continue

                        if m.media is None:
                            for ch in json.loads(AllData[9])[0].split(" "):
                                ch_id = json.loads(AllData[7])[int(ch)]["id"]
                                r = await client.send_message(entity=await client.get_entity(ch_id), message=filtered_text,
                                                              formatting_entities=fd)

                            continue
                        media_path = await download_media(client, m, folders)
                        if media_path is None:
                            continue
                        with open(media_path, 'rb') as f:
                            file = await client.upload_file(file=f)
                        media = await GETmedia_group(client, m, file, media_path)
                        for ch in json.loads(AllData[9])[0].split(" "):
                            ch_id = json.loads(AllData[7])[int(ch)]["id"]
                            r = await client.send_file(entity=await client.get_entity(ch_id), file=media,
                                                               formatting_entities=fd, caption=filtered_text)
                        continue


                # Проверяем, является ли сообщение частью медиагруппы
                media = []
                if m.grouped_id:
                    if m.grouped_id not in processed_groups:
                        media_group = await get_media_group(client, currentId, m.id)

                        media.extend([me.media for me in media_group])
                        processed_groups.append(m.grouped_id)

                # Отправляем сообщение в целевые чаты
                for ch in json.loads(AllData[9])[0].split(" "):
                    ch_id = json.loads(AllData[7])[int(ch)]["id"]
                    filters = filter_data["filters"] or "0"

                    for filt in filters.split():
                        await send_forwarded_message(client, ch_id, filtered_text, m, media, filt)

                await asyncio.sleep(3)

            except AttributeError as e:
                logger.error(f"Ошибка атрибута: {e} — возможно, сообщение не содержит нужные поля.")
            except KeyError as e:
                logger.error(f"Ошибка ключа: {e} — возможно, проблема в данных AllData.")
            except Exception as e:
                logger.error(f"Неизвестная ошибка: {e}")

        await client.disconnect()
        time.sleep(5)

        if os.path.exists(f"./downloads/channel_{currentId}"):
            shutil.rmtree(f"./downloads/channel_{currentId}")

    except Exception as e:
        logger.error(f"action3: {e}")

async def GETmedia_group(client, message, file, path):
    match get_media_type(message.media):
        case "photo":
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedPhoto(
                    file= file,
                    spoiler=getattr(message.media, "spoiler", False)
                )
            ))
            # media = types.InputMediaPhoto(
            #     id=types.InputPhoto(
            #         id=media.photo.id,
            #         access_hash=media.photo.access_hash,
            #         file_reference=media.photo.file_reference
            #     ),
            #     spoiler=getattr(message.media, "spoiler", False)
            # )
        case "gif":
            thumbnail = await get_first_frame(path)
            with open(thumbnail, 'rb') as f:
                thumb = await client.upload_file(file=f)
            width, height, duration = get_video_info(path)
            mime_type, encoding = mimetypes.guess_type(path)
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedDocument(
                    file=file,
                    thumb=thumb,

                    spoiler=getattr(message.media, "spoiler", False),
                    mime_type=mime_type or "video/mp4",
                    attributes=[
                        types.DocumentAttributeVideo(
                            duration=duration,
                            w=width,
                            h=height,
                            nosound=True
                        ),
                        types.DocumentAttributeFilename(file_name=os.path.basename(path))
                    ]
                )
            ))
            # media = types.InputMediaDocument(
            #     id=types.InputDocument(
            #         id=media.document.id,
            #         access_hash=media.document.access_hash,
            #         file_reference=media.document.file_reference
            #     ),
            #     spoiler=getattr(message.media.spoiler, "spoiler", False)
            # )
        case "video":

            thumbnail = await get_first_frame(path)
            with open(thumbnail, 'rb') as f:
                thumb = await client.upload_file(file=f)
            width, height, duration = get_video_info(path)
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedDocument(
                    file=file,
                    thumb=thumb,
                    spoiler=getattr(message.media, "spoiler", False),
                    mime_type=mimetypes.guess_type(path)[0] or "video/mp4",
                    attributes=[
                        types.DocumentAttributeVideo(
                            supports_streaming=True,
                            duration=duration,
                            w=width,
                            h=height
                        ),
                        types.DocumentAttributeFilename(file_name=os.path.basename(path))
                    ]
                )
            ))
            # media = types.InputMediaDocument(
            #     id=types.InputDocument(
            #         id=media.document.id,
            #         access_hash=media.document.access_hash,
            #         file_reference=media.document.file_reference
            #     ),
            #     spoiler=getattr(message.media, "spoiler", False)
            # )
        case "video_note":
            width, height, duration = get_video_info(path)
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedDocument(
                    file=file,
                    spoiler=getattr(message.media, "spoiler", False),
                    mime_type=mimetypes.guess_type(path)[0] or "video/mp4",
                    attributes=[
                        types.DocumentAttributeVideo(
                            duration=duration,
                            w=width,
                            h=height,
                            round_message=True
                        ),
                        types.DocumentAttributeFilename(file_name=os.path.basename(path))
                    ]
                )
            ))
            # media = types.InputMediaDocument(
            #     id=types.InputDocument(
            #         id=media.document.id,
            #         access_hash=media.document.access_hash,
            #         file_reference=media.document.file_reference
            #     )
            # )
        case "audio":
            duration = get_audio_duration(path)
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedDocument(
                    file=file,
                    spoiler=getattr(message.media, "spoiler", False),
                    mime_type=mimetypes.guess_type(path)[0] or "audio/mpeg",
                    attributes=[
                        types.DocumentAttributeAudio(
                            duration=int(duration),
                            title= os.path.basename(path).split(".")[0]
                        ),
                        types.DocumentAttributeFilename(file_name=os.path.basename(path))
                    ]
                )
            ))
            # media = types.InputMediaDocument(
            #     id=types.InputDocument(
            #         id=media.document.id,
            #         access_hash=media.document.access_hash,
            #         file_reference=media.document.file_reference
            #     )
            # )
        case "voice":
            duration = get_audio_duration(path)
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedDocument(
                    file=file,
                    spoiler=getattr(message.media, "spoiler", False),
                    mime_type=mimetypes.guess_type(path)[0] or "audio/mpeg",
                    attributes=[
                        types.DocumentAttributeAudio(
                            duration=int(duration),
                            voice=True
                        ),
                        types.DocumentAttributeFilename(file_name=os.path.basename(path))
                    ]
                )
            ))
            # media = types.InputMediaDocument(
            #     id=types.InputDocument(
            #         id=media.document.id,
            #         access_hash=media.document.access_hash,
            #         file_reference=media.document.file_reference
            #     )
            # )
        case "document":
            media = await client(functions.messages.UploadMediaRequest(
                peer=InputPeerSelf(),
                media=types.InputMediaUploadedDocument(
                    mime_type=mimetypes.guess_type(path)[0] or "application/zip",
                    file=file,
                    attributes=[
                        types.DocumentAttributeFilename(file_name=os.path.basename(path))
                    ]
                )
            ))
            # media = types.InputMediaDocument(
            #     id=types.InputDocument(
            #         id=media.document.id,
            #         access_hash=media.document.access_hash,
            #         file_reference=media.document.file_reference
            #     )
            # )
    return media


########################################################################################

def get_media_type(media):
    if isinstance(media, MessageMediaPhoto):
        return 'photo'
    elif isinstance(media, MessageMediaDocument):
        for attr in media.document.attributes:
            if isinstance(attr, DocumentAttributeAudio):
                return 'audio' if not attr.voice else 'voice'
            if isinstance(attr, DocumentAttributeVideo):
                return 'video_note' if attr.round_message else 'video'
            if isinstance(attr, DocumentAttributeSticker):
                return 'sticker'
        return 'document'
    elif isinstance(media, MessageMediaGeo):
        return 'geo'
    elif isinstance(media, MessageMediaVenue):
        return 'venue'
    elif isinstance(media, MessageMediaContact):
        return 'contact'
    return None

def create_folder_structure(base_path):
    """Создаёт папки для хранения различных типов медиафайлов."""
    folders = {
        "sticker": os.path.join(base_path, "sticker"),
        "photo": os.path.join(base_path, "photos"),
        "video": os.path.join(base_path, "videos"),
        "video_note": os.path.join(base_path, "video_notes"),
        "audio": os.path.join(base_path, "audio"),
        "voice": os.path.join(base_path, "voice"),
        "document": os.path.join(base_path, "documents"),
        "geo": os.path.join(base_path, "geo"),
        "venue": os.path.join(base_path, "venue"),
        "contact": os.path.join(base_path, "contacts"),
    }
    for folder in folders.values():
        os.makedirs(folder, exist_ok=True)
    return folders

def initialize_csv(csv_file):
    """Инициализирует CSV-файл с заголовками, если он ещё не существует."""
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["ID сообщения", "Отправитель", "Текст", "Медиафайл"])  # Заголовки

async def append_to_csv(csv_file, message_id, sender, text, media_path):
    """Добавляет запись о сообщении в CSV."""
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([message_id, sender, text, media_path])


async def download_media(client, message, folders):
    """Скачивает медиафайл и возвращает путь к нему, если файл не существует."""
    media_type = get_media_type(message.media)

    if media_type and media_type in folders:
        # Создаём уникальное имя файла на основе ID сообщения
        filename = f"{message.id}_{media_type}"
        folder_path = folders[media_type]
        file_path = os.path.join(folder_path, filename)
        # Проверяем, существует ли файл
        if glob.glob(file_path+"*"):
            return None  # Пропуск, файл уже существует

        # Скачиваем и сохраняем файл
        saved_path = await client.download_media(message, file=file_path)
        return saved_path
    return None

async def send_or_update_progress(chat_id, total, downloaded, message_id=None):
    """Отправляет или обновляет сообщение о прогрессе через aiogram."""
    text = f"📥 Прогресс загрузки:\n{downloaded} из {total} сообщений обработано."
    try:
        if message_id:  # Обновляем существующее сообщение
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        else:  # Отправляем новое сообщение и закрепляем его
            msg = await bot.send_message(chat_id, text)
            await bot.pin_chat_message(chat_id, msg.message_id, disable_notification=True)
            return msg.message_id
    except:
        logger.info("message is not be modified")


async def Action4(phone, client, AllData):
    """Скачивает медиа и сохраняет сообщения в CSV с прогрессом."""
    try:
        # Инициализация папок и CSV-файла
        channel_id = json.loads(AllData[7])[int(json.loads(AllData[8])[0])]["id"]
        base_path = f"./downloads/channel_{channel_id}"
        folders = create_folder_structure(base_path)
        csv_file = os.path.join(base_path, "messages.csv")
        initialize_csv(csv_file)

        # Получение ID вашего чата
        chat_id = os.getenv("ME_ID")

        # Корректный способ получения количества сообщений
        total_messages = (await client.get_messages(channel_id, limit=0)).total
        downloaded_messages = 0

        # Отправляем сообщение о начале загрузки и закрепляем его
        progress_message_id = await send_or_update_progress(chat_id, total_messages, downloaded_messages)

        startTime = time.time()
        # Перебор всех сообщений в канале
        async for message in client.iter_messages(channel_id):
            media_path = None

            # Скачивание медиафайлов, если они есть
            if message.media:
                media_path = await download_media(client, message, folders)
                if not media_path:
                    continue

            # Получение отправителя
            sender = (await message.get_sender()).username if message.sender_id else "Unknown"

            # Сохранение информации о сообщении в CSV
            await append_to_csv(
                csv_file,
                message_id=message.id,
                sender=sender,
                text=message.text or "",
                media_path=media_path or "N/A"
            )

            downloaded_messages += 1

            # Обновляем прогресс каждые 2 минуты
            if time.time() - startTime >= 30:
                await send_or_update_progress(chat_id, total_messages, downloaded_messages, progress_message_id)
                startTime = time.time()

        # Финальное обновление прогресса
        await bot.edit_message_text(chat_id=chat_id, message_id=progress_message_id, text=f"Загрузка завершена. Файлы сохранены в {base_path}")
        await bot.unpin_chat_message(chat_id, progress_message_id)
        print(f"Загрузка завершена. Файлы сохранены в {base_path}")

    except Exception as e:
        logger.error(f"Ошибка: {e}")



########################################################################################

async def send_message(client, my_channel, mes, event):
    try:
        await client.send_message(
            entity=my_channel,
            file=event,
            message=mes if mes != "" else None,
            parse_mode='markdown',
            link_preview=False
        )
        return True
    except errors.FloodWaitError as e:
        print(f'[!] Ошибка флуда ждем: {e.seconds}')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'[!] Ошибка {e}')
    return False


async def send_Textmessage(client, my_channel, mes, event):
    try:
        await client.send_message(
            entity=my_channel,
            message=mes if mes != "" else None,
            parse_mode='markdown',
            link_preview=False
        )
        return True
    except errors.FloodWaitError as e:
        print(f'[!] Ошибка флуда ждем: {e.seconds}')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'[!] Ошибка {e}')
    return False


async def process_message(client, my_channel, mes, event, media_type_func):
    media_type = media_type_func(
        event.original_update.message.media if hasattr(event.original_update.message, "media") else None)

    if event.grouped_id and media_type:
        await send_message(client, my_channel, mes, event.messages)
        return

    if media_type:
        await send_message(client, my_channel, mes, event.message.media)
        return True


async def process_text_message(client, my_channel, mes, event, pattern):
    if event.grouped_id and event.message.text:
        if re.search(pattern, event.message.text):
            await send_message(client, my_channel, mes, event.messages)
        return

    if event.message.text:
        if re.search(pattern, event.message.text):
            await send_message(client, my_channel, mes, event.message.media)


async def send_FWTextmessage(client, my_channel, mes, entities):
    try:
        await client.send_message(
            formatting_entities=entities,
            entity=my_channel,
            message=mes if mes != "" else None,
            parse_mode='markdown',
            link_preview=False
        )
        return True
    except errors.FloodWaitError as e:
        print(f'[!] Ошибка флуда ждем: {e.seconds}')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'[!] Ошибка {e}')
    return False


async def send_GroupMessage(client, my_channel, mes, event, media, entities):
    try:
        await client.send_message(
            formatting_entities=entities,
            entity=my_channel,
            file=media,
            message=mes if mes != "" else None,
            parse_mode='markdown',
            link_preview=False
        )
        return True
    except errors.FloodWaitError as e:
        print(f'[!] Ошибка флуда ждем: {e.seconds}')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'[!] Ошибка {e}')
    return False


async def send_FWmessage(client, my_channel, mes, event, entities):

    try:
        await client.send_message(
            formatting_entities=entities,
            entity=my_channel,
            file=event,
            message=mes if mes != "" else None,
            parse_mode='markdown',
            link_preview=False
        )
        return True
    except errors.FloodWaitError as e:
        print(f'[!] Ошибка флуда ждем: {e.seconds}')
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.error(f'[!] Ошибка {e}')
    return False


async def process_FWmessage(client, my_channel, mes, event, media, media_type_func):

    if event.grouped_id:
        media_type = any(media_type_func(mas) for mas in media)
        if media_type:
            await send_GroupMessage(client, my_channel, mes, event, media, event.entities)
        return

    if media_type_func(event.media):
        await send_FWmessage(client, my_channel, mes, event.media, event.entities)
        return True


async def process_text_FWmessage(client, my_channel, mes, event, media, pattern):
    if event.grouped_id and event.message.text:
        if re.search(pattern, event.message.text):
            await send_GroupMessage(client, my_channel, mes, event, media, event.entities)
        return

    if event.message.text:
        if re.search(pattern, event.message.text):
            await send_FWmessage(client, my_channel, mes, event, event.entities)


def getAction(phone):
    global url_shorteners
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()
    a = cursor.execute("SELECT * FROM accounts WHERE phone=?", (phone,)).fetchone()
    # Выбираем все записи из таблицы url, где booli равно 'true'
    s = cursor.execute("SELECT badURL FROM url WHERE booli = 'true'").fetchall()

    # Извлекаем все результаты и записываем их в массив
    url_shorteners = [row[0] for row in s]

    connection.commit()
    connection.close()
    return a


async def get_media_group(client: TelegramClient, chat_id, message_id: int):
    # Get messages with id from `id - 9` to `id + 10` to get all possible media group messages.
    messages = await client.get_messages(
        entity=chat_id,
        ids=[msg_id for msg_id in range(message_id - 9, message_id + 10)]
    )

    media_group_id = messages[9].grouped_id if len(messages) == 19 else messages[message_id - 1].grouped_id

    if media_group_id is None:
        print("The message doesn't belong to a media group")
        return
    messages = [msg for msg in messages if msg is not None]
    return [msg for msg in messages if msg.grouped_id == media_group_id]


def get_title_by_id(target_id, data):
    for item in data:
        if item["id"] == target_id:
            return item["title"]
        if item["id"] == int("-100" + str(target_id)):
            return item["title"]
    return None


def replace_ad_links(match):
    url = match.group(0)
    domain = urlparse(url).netloc
    if any(shortener in domain for shortener in url_shorteners):
        return ''
    else:
        return url


###################################################################################################################


def get_video_info(video_path):
    video = cv2.VideoCapture(video_path)

    width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Получение длительности видео
    fps = video.get(cv2.CAP_PROP_FPS)  # частота кадров
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))  # количество кадров
    duration = frame_count / fps  # длительность в секундах

    video.release()
    return width, height, duration


def get_audio_duration(audio_path):
    audio = File(audio_path)
    duration = audio.info.length  # длительность в секундах
    return duration


async def get_first_frame(video_path):
    # Открытие видео
    video = cv2.VideoCapture(video_path)

    # Чтение первого кадра
    success, frame = video.read()

    if success:
        # Сохранение первого кадра как изображения
        cv2.imwrite("first_frame.jpg", frame)

    # Закрытие видеофайла
    video.release()

    return "./first_frame.jpg"


