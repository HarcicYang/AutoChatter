import asyncio
from dataclasses import dataclass
from typing import Union
import time


class MsgCollector:
    def __init__(self, uin: int, delay: float):
        self.uin = uin
        self.delay = delay
        self.hst = []
        self.last = time.time()
        self.task = False

    def add(self, msg: str) -> None:
        if len(self.hst) == 0:
            self.hst.append(msg)
            return

        t = time.time()
        self.hst.append(msg)
        nd = t - self.last
        self.last = t
        if nd > self.delay / 2:
            self.delay += nd / 2
        elif nd < self.delay / 2:
            self.delay -= nd / 2

    async def wait(self) -> None:
        while not self.finished:
            pass

    @property
    def finished(self) -> bool:
        return time.time() - self.last > self.delay


class ChatController:
    def __init__(self):
        self.emotion: float = 51
        self.collectors: dict[int, MsgCollector] = {}

    def update_emotion(self, change: float) -> None:
        self.emotion += change
        if not 0 <= self.emotion <= 100:
            if self.emotion > 100:
                self.emotion = 100
            elif self.emotion < 0:
                self.emotion = 0
            else:
                self.emotion = 52

    async def collect(self, msg: str, uin: int) -> tuple[bool, list[str]]:
        if uin not in self.collectors:
            self.collectors[uin] = MsgCollector(uin, 12)
        self.collectors[uin].add(msg)

        if not self.collectors[uin].task:
            self.collectors[uin].task = True
            await self.collectors[uin].wait()
            res = (True, self.collectors[uin].hst)
            del self.collectors[uin]
            return res
        # if self.collectors[uin].finished:
        #     return True, self.collectors[uin].hst
        else:
            return False, []


@dataclass
class ChatRsp:
    msgs: list[Union[str, float]]
    emotion_change: float


@dataclass
class Sender:
    nickname: str
    uin: int

    def to_json(self) -> dict:
        return self.__dict__
