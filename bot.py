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

def set_id(ch_id, id):
    _ = eval(dB.get(str(ch_id)) or "[]")
    if id not in _:
        _.append(id)
        dB.set(str(ch_id), str(_))

@bot.on(events.NewMessage())
async def auto_post(event):
    th = await event.get_chat()
    id = get_peer_id(th)
    if id not in CHATS.keys():
        return
    try:
        for x in (CHATS.get(id) or []):
            xxx = await event.forward_to(x)
            set_id(x, xxx.id)
    except Exception as error:
        LOGS.error(str(error))

async def checker():
    for x in CHATS.keys():
        for chat in CHATS.get(x):
            for xx in (eval(dB.get(str(chat)) or "[]")):
                try:
                    msg = await bot.get_messages(chat, ids=xx)
                except:
                    msg = None
                if not msg:
                    continue
                try:
                    id = msg.fwd_from.channel_post
                except:
                    id = None
                if id:
                    try:
                        msgg = await bot.get_messages(x, ids=id)
                    except:
                        msgg = None
                    if not msgg:
                        await msg.delete()
          


sch.add_job(checker, "interval", minutes=1)
LOGS.info("Bot Started")
sch.start()
bot.loop.run_forever()




