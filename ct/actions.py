from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class Args:
    ...

    def to_json(self) -> dict:
        raise NotImplementedError


@dataclass
class Action:
    action: str
    args: Args


@dataclass
class NoneArgs(Args):
    ...

    def to_json(self) -> dict:
        return {}


@dataclass
class MsgSendArgs(Args):
    gid: int
    at: bool
    reply: bool
    emotion_change: float
    msgs: list[Union[str, float]]

    def to_json(self) -> dict:
        return self.__dict__
