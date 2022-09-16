import os
import sys
from datetime import datetime as dt
from logging import DEBUG, INFO, basicConfig, getLogger
from traceback import format_exc

from redis import Redis
from telethon import Button, TelegramClient, events
from telethon.utils import get_peer_id
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from var import Var


basicConfig(
    format="[%(levelname)s] [%(asctime)s] [%(name)s] : %(message)s",
    level=INFO,
    datefmt="%m/%d/%Y, %H:%M:%S",
)
LOGS = getLogger(__name__)
TelethonLogger = getLogger("Telethon")
TelethonLogger.setLevel(INFO)


try:
    LOGS.info("Trying Connect With Telegram")
    bot = TelegramClient(None, Var.API_ID, Var.API_HASH).start(bot_token=Var.BOT_TOKEN)
    LOGS.info("Successfully Connected with Telegram")
except Exception as e:
    LOGS.critical("Something Went Wrong While Connecting To Telegram")
    LOGS.error(str(e))
    exit()


try:
    LOGS.info("Trying Connect With Redis database")
    redis_info = Var.REDIS_URI.split(":")
    dB = Redis(
        host=redis_info[0],
        port=redis_info[1],
        password=Var.REDIS_PASSWORD,
        charset="utf-8",
        decode_responses=True,
    )
    LOGS.info("successfully connected to Redis database")
except Exception as eo:
    LOGS.critical("Something Went Wrong While Connecting To Redis")
    LOGS.error(str(eo))
    exit()

CHATS = eval(Var.CHAT.strip())
sch = AsyncIOScheduler()


def set_id(ch_id, sent_id, source_ch_id, source_msg_id):
    data = eval(dB.get(str("FRWD_CHATS")) or "{}")
    if ch_id not in data:
        if sent_id not in data:
            data[ch_id][sent_id] = dict({"chat": source_ch_id, "msg": source_msg_id})
    else:
        data[ch_id] = dict({sent_id: {"chat": source_ch_id, "msg": source_msg_id}})
    dB.set("FRWD_CHATS", str(data))


def del_id(ch_id, send_id):
    data = eval(dB.get(str("FRWD_CHATS")) or "{}")
    if ch_id in list(data):
        if send_id in list(data[ch_id]):
            data[ch_id].pop(send_id)
            if not data[ch_id]:
                data.pop(ch_id)
            dB.set("FRWD_CHATS", str(data))


@bot.on(events.NewMessage(chats=list(CHATS)))
async def auto_post(event):
    ch_id = get_peer_id(event.chat)
    try:
        for chat in CHATS.get(ch_id) or []:
            sent = await event.forward_to(chat)
            set_id(chat, sent.id, ch_id, event.id)
    except Exception as error:
        LOGS.error(str(error))


async def checker():
    data = eval(dB.get(str("FRWD_CHATS")) or "{}")
    for ch_id in list(data):
        for sent_id in list(data[ch_id]):
            try:
                source = await bot.get_messages(
                    data[ch_id][sent_id]["chat"], ids=data[ch_id][sent_id]["msg"]
                )
            except BaseException:
                source = None
            if not source:
                del_id(ch_id, sent_id)
                try:
                    dest = await bot.get_messages(ch_id, ids=sent_id)
                    await dest.delete()
                except BaseException:
                    pass


sch.add_job(checker, "interval", minutes=1)
LOGS.info("Bot Started")
sch.start()
bot.loop.run_forever()
