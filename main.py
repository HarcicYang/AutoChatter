from cfgr.manager import Serializers
import asyncio
import threading
import time

from pywin.Demos.threadedgui import TestThread

from lagrange import Lagrange, install_loguru
from lagrange.client.client import Client
from lagrange.client.events.group import GroupMessage
from lagrange.client.events.service import ServerKick
from lagrange.client.message.elems import At, Text, Quote, Image

from ct.utils.config import ChatterConfig

if True:
    chatter_cfg = ChatterConfig.load_from("config.json", Serializers.JSON, "otto-chatter")

from ct.utils import ChatController, Sender
from ct.events import MsgEvent
from ct.actions import NoneArgs, MsgSendArgs
from ct.api import ChatAPI

ctl = ChatController()
capi = ChatAPI()


def inner_handler(client: Client, event: GroupMessage) -> None:
    msg = ""
    for i in event.msg_chain:
        if type(i) in [Image, Text]:
            msg += i.display

    if not msg:
        return
    print(msg)
    rst, msgs = asyncio.run(ctl.collect(msg, event.uin))
    if not rst:
        return

    rsp = capi.gen(
        MsgEvent(
            time=int(time.time()),
            msg=msgs,
            gid=event.grp_id,
            emotion=ctl.emotion,
            reply_to=None if not isinstance(event.msg_chain[0], Quote) else event.msg_chain[0].msg,
            sender=Sender(
                nickname=event.nickname,
                uin=event.uin
            )
        )
    )

    print(rsp)

    if isinstance(rsp.args, NoneArgs):
        return
    elif isinstance(rsp.args, MsgSendArgs):
        if rsp.args.emotion_change:
            ctl.update_emotion(float(rsp.args.emotion_change))

        for i in rsp.args.msgs:
            if isinstance(i, float) or isinstance(i, int):
                time.sleep(i * 3)
            elif isinstance(i, str):
                if rsp.args.msgs.index(i) == 0:
                    if rsp.args.at:
                        def task():
                            asyncio.run(client.send_grp_msg([At.build(event), Text(i)], event.grp_id))
                    elif rsp.args.reply:
                        def task():
                            asyncio.run(client.send_grp_msg([Quote.build(event), Text(i)], event.grp_id))
                    else:
                        def task():
                            asyncio.run(client.send_grp_msg([Text(i)], event.grp_id))
                else:
                    def task():
                        asyncio.run(client.send_grp_msg([Text(i)], event.grp_id))
                threading.Thread(target=task).start()
        logger.success("Reply succeed")


tasks = []


async def msg_handler(client: Client, event: GroupMessage):
    logger.info(f"{event.nickname} ({event.grp_name}): {event.msg}")
    if event.uin == client.uin or event.grp_id != 623371208:
        return
    threading.Thread(target=lambda: inner_handler(client, event)).start()


async def handle_kick(client: "Client", event: "ServerKick"):
    logger.error(f"被服务器踢出：[{event.title}] {event.tips}")
    await client.stop()


if __name__ == '__main__':
    lag = Lagrange(
        chatter_cfg.lagrange.uin,
        "linux",
        chatter_cfg.lagrange.sign_url
    )
    install_loguru()
    lag.log.set_level("INFO")

    lag.subscribe(GroupMessage, msg_handler)
    lag.subscribe(ServerKick, handle_kick)
    logger = lag.log.fork("lagrange")
    lag.launch()
