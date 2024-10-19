from dataclasses import dataclass

from ct.utils import Sender


@dataclass
class Event:
    time: int

    def to_json(self) -> dict:
        raise NotImplementedError


@dataclass
class MsgEvent(Event):
    msg: list[str]
    gid: int
    emotion: float
    sender: Sender
    reply_to: str

    def to_json(self) -> dict:
        rsp = self.__dict__.copy()
        rsp["sender"] = self.sender.to_json()
        return rsp
